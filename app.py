import streamlit as st
from tax_calculation import TaxInputs, compute_taxes
from database import store_tax_return, retrieve_tax_return

st.set_page_config(page_title="Canadian Income Tax Calculator", layout="centered")

def money_input(label, default="0"):
    value = st.text_input(label, value=default)
    try:
        return float(value) if value.strip() else 0.0
    except ValueError:
        st.error(f"Please enter a valid number for {label}")
        st.stop()
st.markdown(
    """
    <h1 style='text-align: center; white-space: nowrap; font-size: 34px;'>
        Ontario Income Tax Calulator 2025-2026
    </h1>
    """,
    unsafe_allow_html=True
)

choice = st.radio(
    "Choose an option:",
    ["Start New Calculation", "Load Existing Return"]
)

if choice == "Start New Calculation":
    mode = st.radio(
        "Choose mode:",
        ["Guest (Not Saved)", "Login / Saved"]
    )

    name = ""
    phone = ""
    address = ""
    employment_status = "EMPLOYED"

    if mode == "Login / Saved":
        st.subheader("Profile Information")

        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        address = st.text_input("Address")
        employment_status = st.selectbox(
            "Employment Status",
            ["EMPLOYED", "SELF-EMPLOYED", "STUDENT", "UNEMPLOYED", "OTHER"]
        )

    st.subheader("Tax Information")

    employment_income = money_input("Employment Income ($)")
    self_employment_income = money_input("Self-Employment Income ($)")
    income_taxes_paid = money_input("Income Tax Already Paid / Withheld ($)")
    rrsp_fhsa_contrib = money_input("RRSP / FHSA Contributions ($)")
    other_income = money_input("Other Income ($)")
    capital_gains = money_input("Capital Gains ($)")
    eligible_dividends = money_input("Eligible Dividends ($)")
    noneligible_dividends = money_input("Non-Eligible Dividends ($)")

    if st.button("Calculate Tax"):
        tax_input = TaxInputs(
            name=name,
            province="Ontario",
            employment_income=employment_income,
            self_employment_income=self_employment_income,
            other_income=other_income,
            rrsp_fhsa_contrib=rrsp_fhsa_contrib,
            capital_gains=capital_gains,
            eligible_dividends=eligible_dividends,
            noneligible_dividends=noneligible_dividends,
            income_taxes_paid=income_taxes_paid
        )

        result = compute_taxes(tax_input)

        st.subheader("Tax Summary")

        if mode == "Login / Saved":
            st.write(f"**Full Name:** {name}")
            st.write(f"**Phone Number:** {phone}")
            st.write(f"**Address:** {address}")
            st.write(f"**Employment Status:** {employment_status}")

        st.write(f"**Total Income:** ${result.total_income:,.2f}")
        st.write(f"**Taxable Income:** ${result.taxable_income:,.2f}")
        st.write(f"**Federal Tax:** ${result.federal_tax:,.2f}")
        st.write(f"**Ontario Tax:** ${result.ontario_tax:,.2f}")
        st.write(f"**CPP:** ${result.cpp:,.2f}")
        st.write(f"**EI:** ${result.ei:,.2f}")
        st.write(f"**Total Tax:** ${result.total_tax:,.2f}")
        st.write(f"**Net Income:** ${result.net_income:,.2f}")
        st.write(f"**Average Tax Rate:** {result.average_rate * 100:.2f}%")
        st.write(f"**Marginal Tax Rate:** {result.marginal_rate * 100:.2f}%")
        st.write(f"**Estimated Refund / Owing:** ${result.estimated_refund_or_owing:,.2f}")

        if mode == "Login / Saved":
            profile = {
                "phone": phone,
                "address": address,
                "employment_status": employment_status
            }

            tax_id = store_tax_return(tax_input, result, profile)
            st.success(f"Return saved successfully. Your Tax Reference ID is: {tax_id}")

elif choice == "Load Existing Return":
    st.subheader("Load Saved Return")

    tax_id = st.text_input("Enter Tax Reference ID")

    if st.button("Fetch Return"):
        record = retrieve_tax_return(tax_id)

        if record:
            st.success("Return found.")

            st.subheader("Saved Profile")
            st.write(f"**Full Name:** {record.get('name', '')}")
            st.write(f"**Province:** {record.get('province', '')}")

            profile = record.get("profile", {})
            st.write(f"**Phone Number:** {profile.get('phone', '')}")
            st.write(f"**Address:** {profile.get('address', '')}")
            st.write(f"**Employment Status:** {profile.get('employment_status', '')}")

            st.subheader("Saved Tax Summary")
            results = record.get("results", {})
            st.write(f"**Total Income:** ${results.get('total_income', 0):,.2f}")
            st.write(f"**Taxable Income:** ${results.get('taxable_income', 0):,.2f}")
            st.write(f"**Federal Tax:** ${results.get('federal_tax', 0):,.2f}")
            st.write(f"**Ontario Tax:** ${results.get('ontario_tax', 0):,.2f}")
            st.write(f"**CPP:** ${results.get('cpp', 0):,.2f}")
            st.write(f"**EI:** ${results.get('ei', 0):,.2f}")
            st.write(f"**Total Tax:** ${results.get('total_tax', 0):,.2f}")
            st.write(f"**Net Income:** ${results.get('net_income', 0):,.2f}")
            st.write(f"**Average Tax Rate:** {results.get('average_rate', 0) * 100:.2f}%")
            st.write(f"**Marginal Tax Rate:** {results.get('marginal_rate', 0) * 100:.2f}%")
            st.write(f"**Estimated Refund / Owing:** ${results.get('estimated_refund_or_owing', 0):,.2f}")
            st.write(f"**Saved On:** {record.get('timestamp', '')}")
        else:
            st.error("No saved return found with that Tax Reference ID.")