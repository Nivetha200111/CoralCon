"""Tests for the Gmail sender/subject classification helpers.

These guard against the messy extraction we saw on real mail (ATS vendor names
as the company, full subject sentences as the role).
"""

from coralcon.gmail.extractor import _company_from_sender, _role_from_subject


class TestCompanyFromSender:
    def test_plain_recruiting_name(self):
        assert _company_from_sender("Stripe Recruiting <jobs@stripe.com>") == "Stripe"

    def test_strips_talent_acquisition_keeps_acronym(self):
        assert _company_from_sender(
            "IBM Talent Acquisition <noreply@us-greenhouse-mail.io>"
        ) == "IBM"

    def test_via_workday(self):
        assert _company_from_sender(
            "Logitech via Workday <do-not-reply@myworkday.com>"
        ) == "Logitech"

    def test_lowercase_display_name_is_titlecased(self):
        assert _company_from_sender(
            '"louis vuitton talents" <careers@louisvuitton.com>'
        ) == "Louis Vuitton"

    def test_falls_back_to_domain(self):
        assert _company_from_sender("careers@scale.com") == "Scale"

    def test_pure_ats_sender_is_unknown(self):
        # No company signal anywhere -> Unknown, never the vendor name.
        assert _company_from_sender("Workday <noreply@myworkdayjobs.com>") == "Unknown"
        assert _company_from_sender("<no-reply@greenhouse.io>") == "Unknown"


class TestRoleFromSubject:
    def test_extracts_concise_title_not_sentence(self):
        assert _role_from_subject(
            "Your application for our Software Engineer"
        ) == "Software Engineer"

    def test_keeps_seniority(self):
        assert _role_from_subject("Senior Backend Engineer - update") == "Senior Backend Engineer"

    def test_stops_at_comma(self):
        assert _role_from_subject("Data Analyst, South Asia") == "Data Analyst"

    def test_no_role_returns_empty(self):
        assert _role_from_subject("Update on your application") == ""
        assert _role_from_subject("We regret to inform you") == ""
