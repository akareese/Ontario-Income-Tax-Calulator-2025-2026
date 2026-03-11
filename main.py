from __future__ import annotations

from tax_calculation import TaxInputs, compute_taxes
from database import store_tax_return, retrieve_tax_return


def money(x: float) -> str:
    return f"${x:,.2f}"


def read_float(prompt: str, min_value: float = 0.0) -> float:
    while True:
        raw = input(prompt).strip().replace(",", "")
        if raw == "":
            raw = "0"
        try:
            val = float(raw)
            if val < min_value:
                print(f"Enter a value >= {min_value}.")
                continue
            return val
        except ValueError:
            print("Enter a valid number (e.g., 85000 or 85,000).")


def read_choice(prompt: str, choices: tuple[str, ...]) -> str:
    choices_set = {c.upper() for c in choices}
    while True:
        val = input(prompt).strip().upper()
        if val in choices_set:
            return val
        print(f"Choose one of: {', '.join(choices)}")


def read_nonempty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("This field can’t be blank.")


def collect_tax_inputs(name: str, province: str = "ON") -> TaxInputs:
    print("\nEnter your tax information (press Enter for 0 on numeric fields).")

    employment = read_float("Employment income ($): ")
    self_emp = read_float("Self-employment income ($): ")
    taxes_paid = read_float("Income tax already paid/withheld ($): ")

    rrsp = read_float("RRSP / FHSA contributions ($): ")

    other_income = read_float("Other income ($): ")
    capital_gains = read_float("Capital gains ($): ")
    eligible_div = read_float("Eligible dividends ($): ")
    noneligible_div = read_float("Non-eligible dividends ($): ")

    return TaxInputs(
        name=name,
        province=province,
        employment_income=employment,
        self_employment_income=self_emp,
        other_income=other_income,
        rrsp_fhsa_contrib=rrsp,
        capital_gains=capital_gains,
        eligible_dividends=eligible_div,
        noneligible_dividends=noneligible_div,
        income_taxes_paid=taxes_paid,
    )


def print_results(result) -> None:
    print("\n===== TAX SUMMARY =====\n")

    print("Total income:       ", money(result.total_income))
    print("Taxable income:     ", money(result.taxable_income))

    print("\n--- Taxes ---")
    print("Federal tax:        ", money(result.federal_tax))
    print("Ontario tax:        ", money(result.ontario_tax))
    print("CPP:                ", money(result.cpp))
    print("EI:                 ", money(result.ei))
    print("Total tax:          ", money(result.total_tax))

    print("\nNet income:         ", money(result.net_income))
    print("Average tax rate:   ", f"{result.average_rate * 100:.2f}%")
    print("Marginal tax rate:  ", f"{result.marginal_rate * 100:.2f}% (simplified)")

    print("\n--- Refund / Owing (estimate) ---")
    if result.estimated_refund_or_owing >= 0:
        print("Estimated refund:   ", money(result.estimated_refund_or_owing))
    else:
        print("Estimated owing:    ", money(abs(result.estimated_refund_or_owing)))


def collect_login_profile() -> dict:
    print("\n=== Login Mode (Saved Return) ===")
    name = read_nonempty("Full name: ")
    phone = read_nonempty("Phone number: ")
    address = read_nonempty("Address: ")

    employment_status = read_choice(
        "Employment status [EMPLOYED/SELF-EMPLOYED/STUDENT/UNEMPLOYED/OTHER]: ",
        ("EMPLOYED", "SELF-EMPLOYED", "STUDENT", "UNEMPLOYED", "OTHER"),
    )

    return {
        "name": name,
        "phone": phone,
        "address": address,
        "employment_status": employment_status,
    }


def guest_name_choice() -> str:
    print("\n=== Guest Mode (Not Saved) ===")
    choice = read_choice(
        "Continue as (1) Anonymous guest or (2) Enter a display name? [1/2]: ",
        ("1", "2"),
    )
    if choice == "1":
        return "Anonymous"
    return read_nonempty("Display name: ")


def load_existing_return() -> None:
    tax_id = input("Enter your Tax Reference ID (ex: TX-2026-8F3A-K21D): ").strip().upper()
    record = retrieve_tax_return(tax_id)

    if not record:
        print("Not found. Double-check the ID and try again.")
        return

    print("\n=== Loaded Return ===")
    print("Name:      ", record.get("name", ""))
    print("Province:  ", record.get("province", ""))
    print("Timestamp: ", record.get("timestamp", ""))

    profile = record.get("profile", {})
    if profile:
        print("Phone:     ", profile.get("phone", ""))
        print("Address:   ", profile.get("address", ""))
        print("Status:    ", profile.get("employment_status", ""))

    results = record.get("results", {})
    if results:
        print("\n--- Saved Results ---")
        for k in [
            "total_income",
            "taxable_income",
            "federal_tax",
            "ontario_tax",
            "cpp",
            "ei",
            "total_tax",
            "net_income",
            "average_rate",
            "marginal_rate",
            "estimated_refund_or_owing",
        ]:
            if k in results:
                v = results[k]
                if isinstance(v, (int, float)) and "rate" not in k:
                    print(f"{k:>26}: {money(float(v))}")
                elif "rate" in k:
                    print(f"{k:>26}: {float(v) * 100:.2f}%")
                else:
                    print(f"{k:>26}: {v}")
    else:
        print("\n(Record loaded, but results missing.)")


def main() -> None:
    print("\n== Ontario + Federal Income Tax Calculator (2025–2026) ==\n")

    choice = input(
        "Do you want to (1) start a new calculation or (2) load an existing one? [1/2]: "
    ).strip()

    if choice == "2":
        load_existing_return()
        return

    mode = read_choice(
        "Choose mode: (1) Guest (not saved) or (2) Login (saved) [1/2]: ",
        ("1", "2"),
    )

    province = "ON"

    if mode == "1":
        name = guest_name_choice()
        inputs = collect_tax_inputs(name=name, province=province)
        result = compute_taxes(inputs)
        print_results(result)

        print("\nGuest mode: this return was NOT saved.")
        return

    profile = collect_login_profile()
    inputs = collect_tax_inputs(name=profile["name"], province=province)
    result = compute_taxes(inputs)

    tax_id = store_tax_return(inputs, result, profile)

    print_results(result)

    print("\nYour Tax Reference ID:", tax_id)
    print("Save this ID to retrieve your tax calculation later.")

    print("\n(Login profile collected and saved)")
    print("Phone:", profile["phone"])
    print("Address:", profile["address"])
    print("Employment status:", profile["employment_status"])


if __name__ == "__main__":
    main()
