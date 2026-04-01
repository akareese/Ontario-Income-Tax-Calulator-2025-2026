from dataclasses import dataclass
from typing import Tuple


@dataclass
class TaxInputs:
    name: str
    province: str

    employment_income: float
    self_employment_income: float
    other_income: float

    rrsp_fhsa_contrib: float

    capital_gains: float
    eligible_dividends: float
    noneligible_dividends: float

    income_taxes_paid: float


@dataclass
class TaxResult:
    total_income: float
    taxable_income: float

    federal_tax: float
    ontario_tax: float

    cpp: float
    ei: float

    total_tax: float
    net_income: float

    average_rate: float
    marginal_rate: float

    estimated_refund_or_owing: float



def bracket_tax(income: float, brackets: Tuple[Tuple[float, float, float], ...]) -> float:
    tax = 0.0
    for lower, upper, rate in brackets:
        if income <= lower:
            break
        amt = min(income, upper) - lower
        if amt > 0:
            tax += amt * rate
    return tax


def marginal_rate(income: float, brackets: Tuple[Tuple[float, float, float], ...]) -> float:
    if income <= 0:
        return 0.0
    for lower, upper, rate in brackets:
        if lower < income <= upper:
            return rate
    return brackets[-1][2]


def nonrefundable_credit(amount: float, rate: float) -> float:
    return amount * rate


def compute_cpp_ei(employment_income: float, self_employment_income: float):

    earned = employment_income + self_employment_income

    CPP_RATE = 0.0595
    CPP_BASIC_EXEMPTION = 3500
    CPP_MAX_PENSIONABLE = 68500

    EI_RATE = 0.0166
    EI_MAX_INSURABLE = 63000

    pensionable = max(0, min(earned, CPP_MAX_PENSIONABLE) - CPP_BASIC_EXEMPTION)
    cpp = pensionable * CPP_RATE

    insurable = min(earned, EI_MAX_INSURABLE)
    ei = insurable * EI_RATE

    return cpp, ei


def compute_federal_ontario_tax(taxable_income: float):

    FED_BRACKETS = (
        (0, 55867, 0.15),
        (55867, 111733, 0.205),
        (111733, 173205, 0.26),
        (173205, 246752, 0.29),
        (246752, float("inf"), 0.33)
    )

    FED_BPA = 15705
    FED_RATE = 0.15

    ON_BRACKETS = (
        (0, 51446, 0.0505),
        (51446, 102894, 0.0915),
        (102894, 150000, 0.1116),
        (150000, 220000, 0.1216),
        (220000, float("inf"), 0.1316)
    )

    ON_BPA = 12399
    ON_RATE = 0.0505

    fed_tax = bracket_tax(taxable_income, FED_BRACKETS)
    on_tax = bracket_tax(taxable_income, ON_BRACKETS)

    fed_credit = nonrefundable_credit(FED_BPA, FED_RATE)
    on_credit = nonrefundable_credit(ON_BPA, ON_RATE)

    fed_tax = max(0, fed_tax - fed_credit)
    on_tax = max(0, on_tax - on_credit)

    fed_marg = marginal_rate(taxable_income, FED_BRACKETS)
    on_marg = marginal_rate(taxable_income, ON_BRACKETS)

    return fed_tax, on_tax, fed_marg + on_marg


def compute_taxes(inp: TaxInputs) -> TaxResult:

    total_income = (
        inp.employment_income +
        inp.self_employment_income +
        inp.other_income +
        inp.capital_gains +
        inp.eligible_dividends +
        inp.noneligible_dividends
    )

    taxable_income = max(0, total_income - inp.rrsp_fhsa_contrib)

    fed_tax, on_tax, marginal = compute_federal_ontario_tax(taxable_income)

    cpp, ei = compute_cpp_ei(inp.employment_income, inp.self_employment_income)

    total_tax = fed_tax + on_tax + cpp + ei

    net_income = total_income - total_tax

    avg_rate = total_tax / total_income if total_income > 0 else 0

    refund_or_owing = inp.income_taxes_paid - total_tax

    return TaxResult(
        total_income,
        taxable_income,
        fed_tax,
        on_tax,
        cpp,
        ei,
        total_tax,
        net_income,
        avg_rate,
        marginal,
        refund_or_owing
    )