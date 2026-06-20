"""Paper Submission Agent"""
import datetime

JOURNALS_DB = {
    "RSE": {"if": 13.5, "accept_rate": 20},
    "ISPRS_JPRS": {"if": 12.7, "accept_rate": 22},
    "IJAEOG": {"if": 7.5, "accept_rate": 25},
    "JAG": {"if": 7.5, "accept_rate": 25},
    "Ecological_Indicators": {"if": 6.9, "accept_rate": 25},
    "STOTEN": {"if": 10.8, "accept_rate": 30},
    "Remote_Sensing": {"if": 5.0, "accept_rate": 40},
    "Land": {"if": 3.9, "accept_rate": 45},
    "GIScience_RS": {"if": 6.7, "accept_rate": 25},
    "IEEE_TGRS": {"if": 8.2, "accept_rate": 25},
    "IEEE_GRSL": {"if": 4.0, "accept_rate": 35},
    "JSTARS": {"if": 4.2, "accept_rate": 35},
    "Nature": {"if": 64.8, "accept_rate": 8},
    "Science": {"if": 56.9, "accept_rate": 7},
}


class PaperSubmissionAgent:
    def __init__(self):
        self.journals = JOURNALS_DB

    def recommend(self, topic="", target_if=None):
        candidates = list(self.journals.keys())
        journals = [{"name": n, **self.journals[n]} for n in candidates]
        if target_if:
            aspiration = sorted([j for j in journals if j["if"] >= target_if], key=lambda x: -x["if"])[:3]
            safe = sorted([j for j in journals if j["if"] < target_if - 2], key=lambda x: -x["accept_rate"])[:3]
        else:
            aspiration = sorted(journals, key=lambda x: -x["if"])[:3]
            safe = sorted(journals, key=lambda x: -x["accept_rate"])[:3]
        medium = [j for j in journals if j not in aspiration and j not in safe][:3]
        return {"aspiration": aspiration, "medium": medium, "safe": safe}

    def predict(self, journal_name, novelty=5, methods=5, scope=5):
        j = self.journals.get(journal_name)
        if not j:
            return {"error": f"Unknown journal: {journal_name}"}
        base = j["accept_rate"] / 100.0
        score = base + (novelty/10.0*0.15) + (methods/10.0*0.15) + (scope/10.0*0.15)
        score = min(max(score, 0.02), 0.95)
        return {
            "journal": journal_name,
            "IF": j["if"],
            "accept_prob": round(score*100, 1),
            "desk_reject_prob": round((1-score)*0.6*100, 1),
        }

    def cover_letter(self, title, authors, journal_name, significance):
        d = datetime.datetime.now().strftime("%B %d, %Y")
        a_str = ", ".join(authors) if authors else "[Authors]"
        txt = f"### Cover Letter - {journal_name}\nDate: {d}\n\n"
        txt += f"Dear Editor,\n\nWe submit {title} for publication in {journal_name}.\n\n"
        txt += f"This study presents {significance}.\n\n"
        txt += "We confirm no conflicts of interest.\n\nSincerely,\n"
        txt += a_str
        return txt


if __name__ == "__main__":
    a = PaperSubmissionAgent()
    r = a.recommend(target_if=5.0)
    for t, js in r.items():
        print(f"\n{t.upper()}:")
        for j in js: print(f'  {j["name"]} (IF={j["if"]}, AR={j["accept_rate"]}%)')