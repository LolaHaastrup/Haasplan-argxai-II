"""
presenter.py
============

Turns the dialogue's moves into text a participant can follow without any
other page open beside it.

WHY THIS EXISTS
---------------
The supervisor's review of the app found that answers were not self-contained.
An ordering was named "1 before 2" with no sign of which actions those were.
"Reversal" was never defined. P1, P2 and C were never explained. A participant
who could not follow would, in her words, give all negative answers. So every
answer is now written so that it can be understood on its own: it names the
actions, says what a scheme is, spells out each premise and the conclusion in
full, and defines "reversing an order" where that idea appears.

WHAT IT DOES NOT TOUCH
----------------------
This is display only. The protocol in explanation_dialogue.py decides which
moves are legal and what the system says, exactly as before. The data files
are unchanged, and the stored transcript keeps the framework's own wording, so
the analysis and the notebook's hash check are unaffected by anything here.

Where this module wording differs from the data, the data is the source of
truth and this module is a paraphrase of it. Every rewrite below starts from a
label or detail string that the framework produced.
"""

import re
from typing import Dict, List, Optional, Tuple

import plain
import schemes as sch
from explanation_dialogue import Locution

REVERSAL_NOTE = ("(Reversing an order means swapping it, so that the action "
                 "that was meant to come second runs first.)")

SCHEME_REMINDER = ("A scheme lists premises, the assumptions it relies on, "
                   "followed by a conclusion, what those premises establish "
                   "together.")


def nice_name(action_name: str) -> str:
    """bus_travel -> Bus travel. Used when a domain supplies no display name."""
    text = (action_name or "").replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else text


def cap(text: str) -> str:
    """Capitalise the first letter unless the sentence opens with bold."""
    if not text or text.startswith("**"):
        return text
    return text[0].upper() + text[1:]


def node_indices(node: Optional[str]) -> List[int]:
    """Action indices named in a node id such as CQ6@Action(3, 4)."""
    part = str(node or "").split("@", 1)[-1]
    return [int(x) for x in re.findall(r"\d+", part)]


class Presenter:
    """Writes the on-screen text for one dialogue."""

    def __init__(self, dialogue, display_names: Optional[Dict[str, str]] = None):
        self.d = dialogue
        self.cq_meta = dialogue.cq_meta
        self.by_index: Dict[int, str] = {}
        self.index_of: Dict[str, int] = {}
        self.window: Dict[int, Tuple[float, float]] = {}
        names = dict(display_names or {})
        for step in dialogue.steps:
            idx = step.get("action_index", step.get("step_index"))
            raw = step.get("action_name", "")
            label = (step.get("display_name") or names.get(raw)
                     or nice_name(raw))
            if label == raw:
                label = nice_name(raw)
            self.by_index[idx] = label
            self.index_of[raw] = idx
            self.window[idx] = (step.get("start"), step.get("end"))
        self.raw_to_label = {raw: self.by_index[i]
                             for raw, i in self.index_of.items()}

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def short(self, i: Optional[int]) -> str:
        """Just the bold name, for second and later mentions."""
        if i is None:
            return "the action"
        return "**%s**" % self.by_index.get(i, "action %s" % i)

    def act(self, i: Optional[int]) -> str:
        """Bold name plus its number, for the first mention."""
        if i is None:
            return "the action"
        return "**%s** (action %s)" % (self.by_index.get(i, "action %s" % i), i)

    def act_raw(self, raw: str) -> str:
        """First mention, from a raw action identifier."""
        if raw in self.index_of:
            return self.act(self.index_of[raw])
        return "**%s**" % nice_name(raw)

    def short_raw(self, raw: str) -> str:
        if raw in self.index_of:
            return self.short(self.index_of[raw])
        return "**%s**" % nice_name(raw)

    def _fluent(self, expr: str) -> str:
        return plain.fluent(expr)

    def _q(self, expr: str) -> str:
        """A fluent as a quoted clause, so it reads as a noun inside a sentence."""
        return "\u201c%s\u201d" % plain.fluent(expr)

    def sname(self, scheme_id: str) -> str:
        """S1 Action Applicability, so a bare id is never left unexplained."""
        short = sch.SCHEMES.get(scheme_id, ("", ""))[0]
        return "%s %s" % (scheme_id, short) if short else scheme_id

    def _name_schemes(self, text: str, skip=()) -> str:
        """Give each scheme id its name at first mention in a paragraph."""
        done = set(skip)
        def repl(match):
            sid = match.group(0)
            if sid in done or sid not in sch.SCHEMES:
                return sid
            done.add(sid)
            return self.sname(sid)
        return re.sub(r"\bS\d\b", repl, text)

    def _ordering(self, record: dict, idx: List[int]) -> Optional[Tuple[int, int]]:
        """The (earlier, later) pair an ordering answer is about."""
        match = re.search(r"ordering (\d+) before (\d+)",
                          record.get("Defeating conclusion", "") or "")
        if match:
            return int(match.group(1)), int(match.group(2))
        if len(idx) == 2:
            return idx[0], idx[1]
        return None

    def _clean_text(self, text: str) -> str:
        """Plain-language pass for free text written by the framework."""
        out = plain.render(text or "", self.raw_to_label)
        out = out.replace("the replayed state",
                          "the state of the world worked out from the plan")
        out = out.replace("replayed state",
                          "state of the world worked out from the plan")
        return out

    # ------------------------------------------------------------------
    # The question a participant asks
    # ------------------------------------------------------------------

    def question(self, cq: str, idx: List[int]) -> str:
        """The critical question, with the actions it concerns named."""
        a = idx[0] if idx else None
        b = idx[1] if len(idx) > 1 else None
        A, Ah = self.act(a), self.short(a)
        B, Bh = self.act(b), self.short(b)
        pair = b is not None
        if cq == "CQ1":
            return ("Did everything %s needs in order to start hold at the "
                    "moment it was scheduled to start?" % A)
        if cq == "CQ2":
            return ("Does every condition that must stay true while %s runs "
                    "stay true for the whole time it runs?" % A)
        if cq == "CQ3":
            return ("Does %s produce something the plan genuinely needs, "
                    "either a condition a later action requires or part of "
                    "the goal?" % A)
        if cq == "CQ4":
            return ("Did every action that produces something %s needs finish "
                    "before %s was scheduled to start?" % (A, Ah))
        if cq == "CQ5":
            return ("Does the scheduled time of %s obey all outside timing "
                    "rules, such as release times, deadlines and minimum "
                    "gaps?" % A)
        if cq == "CQ6" and pair:
            return ("Can %s and %s, which run at the same time, each legally "
                    "begin at the moment their times start to overlap?"
                    % (A, B))
        if cq == "CQ7" and pair:
            return ("Do %s and %s, which run at the same time, use different "
                    "exclusive resources, and avoid interfering with "
                    "conditions the other needs to stay true?" % (A, B))
        if cq == "CQ8" and pair:
            return ("Would reversing or removing the order of %s before %s "
                    "leave a condition %s needs missing, or make the goal "
                    "unreachable? %s" % (A, B, Bh, REVERSAL_NOTE))
        if cq == "CQ9":
            return ("Does any action running at the same time as %s remove a "
                    "condition that must stay true while %s runs?" % (A, Ah))
        meta = self.cq_meta.get(cq, {})
        text = self._clean_text(meta.get("challenge", cq))
        if idx:
            text += " (about %s)" % " and ".join(self.act(i) for i in idx)
        return text

    def user_text(self, move) -> str:
        """What the participant is shown as having said."""
        if move.locution is Locution.CHALLENGE:
            return "**%s.** %s" % (move.content["cq"],
                                   self.question(move.content["cq"],
                                                 node_indices(move.target)))
        if move.locution is Locution.WHY:
            node = move.content.get("node")
            premise = move.content.get("premise", {})
            sentence = self.premise_sentence(
                premise.get("label", ""), premise.get("detail", ""),
                self._context(node))
            return "Why does this hold? %s" % sentence
        if move.locution is Locution.OPEN:
            return "Explain why this plan is valid."
        return plain.render(move.text, self.raw_to_label)

    # ------------------------------------------------------------------
    # Context for one node
    # ------------------------------------------------------------------

    def _context(self, node: Optional[str]) -> dict:
        record = self.d._by_node.get(node, {}) if node else {}
        idx = node_indices(node)
        return {"idx": idx, "record": record,
                "ord": self._ordering(record, idx) if record else None}

    # ------------------------------------------------------------------
    # Premises and conclusions of a scheme, in full sentences
    # ------------------------------------------------------------------

    def premise_sentence(self, label: str, detail: str, ctx: dict) -> str:
        label = (label or "").strip()
        detail = (detail or "").strip()
        idx = ctx.get("idx", [])
        a = idx[0] if idx else None
        b = idx[1] if len(idx) > 1 else None
        A, Ah = self.act(a), self.short(a)
        B = self.act(b)
        order = ctx.get("ord")

        def finish(text: str) -> str:
            return cap(text)

        m = re.fullmatch(r"Start: (.+)", label)
        if m:
            return finish("before %s starts, %s (a condition it needs)."
                          % (A, self._fluent(m.group(1))))

        m = re.fullmatch(r"Invariant: (.+) holds over \((\d+),\s*(\d+)\)", label)
        if m:
            return finish("%s has to stay true while %s runs, and it does, "
                          "from time %s to time %s."
                          % (self._q(m.group(1)), Ah, m.group(2),
                             m.group(3)))

        m = re.fullmatch(r"Invariant inv\((\w+)\) = \{(.+)\} exists", label)
        if m:
            return finish("%s has a condition that must stay true while it "
                          "runs: %s." % (self.act_raw(m.group(1)),
                                         self._q(m.group(2))))

        m = re.fullmatch(r"(.+) holds and is not deleted over "
                         r"\((\d+),\s*(\d+)\)", label)
        if m:
            return finish("%s is true throughout time %s to time %s, and no "
                          "other action removes it in that time."
                          % (self._q(m.group(1)), m.group(2), m.group(3)))

        m = re.fullmatch(r"Disruption would invalidate (\w+) and make G "
                         r"unreachable", label)
        if m:
            return finish("if that condition were removed, %s could not run "
                          "and the goal could not be reached."
                          % self.short_raw(m.group(1)))

        m = re.fullmatch(r"(\w+) present", label)
        if m:
            return finish("%s is part of the plan." % self.act_raw(m.group(1)))

        m = re.fullmatch(r"(?:Internal applicability|Action applicable) "
                         r"\((S\d)\)", label)
        if m:
            return finish("%s could legally run when it was scheduled "
                          "(this is what scheme %s establishes)."
                          % (A, self.sname(m.group(1))))

        if label == "No deadline constraint (vacuous)":
            return finish("%s has no deadline of its own to meet, so there is "
                          "nothing to check here." % A)
        if label == "No end conditions (vacuous)":
            return finish("%s has no condition that must be true when it "
                          "ends, so there is nothing to check here." % A)
        if label == "No over-all invariants (vacuous)":
            return finish("%s has no condition that must stay true while it "
                          "runs, so there is nothing to check here." % A)
        if label == "No concurrent actions (vacuous)":
            return finish("nothing else runs at the same time as %s." % A)

        m = re.fullmatch(r"Plan completes at makespan t=(\d+)", label)
        if m:
            return finish("the whole plan finishes at time %s." % m.group(1))

        m = re.fullmatch(r"Enabling: e\((\w+)\)=([\d.]+) <= s\((\w+)\)=([\d.]+)",
                         label)
        if m:
            return finish("%s finishes at time %s and %s starts at time %s, "
                          "so %s is finished before %s starts."
                          % (self.act_raw(m.group(1)), m.group(2),
                             self.act_raw(m.group(3)), m.group(4),
                             self.short_raw(m.group(1)),
                             self.short_raw(m.group(3))))

        m = re.fullmatch(r"Ordering: e\(Action (\d+)\)=([\d.]+) <= "
                         r"s\(Action (\d+)\)=([\d.]+)", label)
        if m:
            first, second = int(m.group(1)), int(m.group(3))
            return finish("%s finishes at time %s and %s starts at time %s, "
                          "so %s is finished before %s starts."
                          % (self.act(first), m.group(2), self.act(second),
                             m.group(4), self.short(first),
                             self.short(second)))

        m = re.fullmatch(r"Deadline: e\((\w+)\)=([\d.]+) <= ([\d.]+)", label)
        if m:
            return finish("%s finishes at time %s, which is within its "
                          "deadline of time %s."
                          % (self.act_raw(m.group(1)), m.group(2), m.group(3)))

        m = re.fullmatch(r"(\w+) produces effect needed by (\w+)", label)
        if m:
            fl = re.search(r"(?:the fluent|provides) (.+)", detail)
            thing = self._q(fl.group(1)) if fl else "something"
            return finish("%s produces the following, which %s needs in order "
                          "to start: %s." % (self.act_raw(m.group(1)),
                                             self.short_raw(m.group(2)),
                                             thing))

        m = re.fullmatch(r"Reversal would remove a required start condition "
                         r"\((.+)\)", label)
        if m:
            fl = self._q(m.group(1))
            if order:
                early, late = order
                return finish("if the order were reversed, so that %s ran "
                              "before %s, then %s would not yet be true when "
                              "%s needed it to start."
                              % (self.act(late), self.act(early), fl,
                                 self.short(late)))
            return finish("if the order were reversed, %s would not yet be "
                          "true when the later action needed it to start." % fl)

        m = re.fullmatch(r"Effect '(.+)' produced", label)
        if m:
            return finish("%s produces the following: %s."
                          % (A, self._q(m.group(1))))

        if label == "Effect consumed or satisfies G":
            steps = re.findall(r"\d+", detail)
            if steps:
                return finish("what it produces is needed later, by %s."
                              % " and ".join(self.act(int(s)) for s in steps))
            return finish("what it produces is part of the goal.")

        m = re.fullmatch(r"Intervals overlap: \[(\d+),\s*(\d+)\] and "
                         r"\[(\d+),\s*(\d+)\]", label)
        if m:
            return finish("%s runs from time %s to time %s, and %s runs from "
                          "time %s to time %s, so they overlap."
                          % (A, m.group(1), m.group(2), B, m.group(3),
                             m.group(4)))

        m = re.fullmatch(r"(\w+) individually applicable \((S\d)\)", label)
        if m:
            return finish("%s could legally start on its own (this is what "
                          "scheme %s establishes)."
                          % (self.act_raw(m.group(1)), m.group(2)))

        m = re.fullmatch(r"(S\d) holds for the pair", label)
        if m:
            return finish("scheme %s holds: %s and %s could each legally "
                          "begin when their times start to overlap."
                          % (self.sname(m.group(1)), A, B))

        m = re.fullmatch(r"No resource conflict: disjoint exclusive resource "
                         r"locks \((.+) and (.+)\)", label)
        if m:
            r1 = "no exclusive resource" if m.group(1) == "None" else m.group(1)
            r2 = "no exclusive resource" if m.group(2) == "None" else m.group(2)
            return finish("%s and %s do not compete for a resource: %s uses "
                          "%s and %s uses %s."
                          % (A, B, self.short(a), r1, self.short(b), r2))

        if label.startswith("Mutual invariant compatibility"):
            return finish("neither of the two actions removes a condition "
                          "that the other needs to stay true while it runs.")

        m = re.fullmatch(r"Concurrency justified: (\d+) < (\d+)", label)
        if m:
            return finish("running them together takes %s time units, "
                          "against %s if they ran one after the other, so "
                          "overlapping them saves time."
                          % (m.group(1), m.group(2)))

        text = self._clean_text(label)
        if detail:
            text += " " + self._clean_text(detail)
        text = text.strip()
        return cap(text if text.endswith(".") else text + ".")

    def conclusion_sentence(self, record: dict, ctx: dict) -> str:
        raw = (record.get("Defeating conclusion") or "").strip()
        idx = ctx.get("idx", [])
        a = idx[0] if idx else None
        b = idx[1] if len(idx) > 1 else None
        cq = record.get("CQ", "")

        m = re.fullmatch(r"(\w+) is temporally feasible\.", raw)
        if m:
            return ("Therefore %s is temporally feasible: its timing works."
                    % self.act_raw(m.group(1)))
        m = re.fullmatch(r"(\w+) is applicable over \[(\d+),\s*(\d+)\]\.", raw)
        if m:
            return ("Therefore %s could legally run for its whole scheduled "
                    "time, from time %s to time %s."
                    % (self.act_raw(m.group(1)), m.group(2), m.group(3)))
        m = re.fullmatch(r"The ordering (\d+) before (\d+) is necessary\.", raw)
        if m:
            return ("Therefore the ordering of %s before %s is necessary."
                    % (self.act(int(m.group(1))), self.act(int(m.group(2)))))
        m = re.fullmatch(r"The invariant (.+) is maintained throughout "
                         r"(\w+)\.", raw)
        if m:
            return ("Therefore %s is maintained throughout %s: it stays true "
                    "for the whole time %s runs."
                    % (self._q(m.group(1)), self.act_raw(m.group(2)),
                       self.short_raw(m.group(2))))
        m = re.fullmatch(r"(\w+) contributes causally to G\.", raw)
        if m:
            return ("Therefore %s contributes causally to the goal: something "
                    "it produces is needed later or is part of the goal."
                    % self.act_raw(m.group(1)))
        if raw == "Running the pair concurrently is safe and beneficial.":
            return ("Therefore running %s and %s at the same time is safe, "
                    "and it is beneficial because it saves time."
                    % (self.act(a), self.act(b)))
        if raw == "Both actions may legally begin at the overlap start.":
            return ("Therefore %s and %s may both legally begin at the "
                    "moment their times start to overlap."
                    % (self.act(a), self.act(b)))
        if raw:
            return "Therefore " + self._clean_text(raw)[:1].lower() + \
                self._clean_text(raw)[1:]
        if cq == "CQ5":
            return ("Therefore the scheduled time of %s respects the outside "
                    "timing rules that apply to it." % self.act(a))
        return "Therefore the challenge is answered."

    # ------------------------------------------------------------------
    # The system's replies
    # ------------------------------------------------------------------

    def reply_text(self, reply) -> str:
        loc = reply.locution
        if loc is Locution.ASSERT:
            return self._summary()
        if loc is Locution.JUSTIFY:
            return self._justify(reply)
        if loc is Locution.CONCEDE:
            return self._concede(reply)
        if loc is Locution.DECLARE_NA:
            return self._not_applicable(reply)
        if loc is Locution.GROUND:
            return self._ground(reply)
        if loc is Locution.REFORMULATE:
            return self._reformulate(reply)
        if loc is Locution.CLOSE:
            return "Dialogue closed. " + self.closing_summary()
        return plain.render(reply.text, self.raw_to_label)

    def _summary(self) -> str:
        s8 = self.d.s8_result
        premises = s8.get("premises", [])
        lines = []
        for i, premise in enumerate(premises, 1):
            pid = sch.premise_id(i)
            mark = "holds" if premise.get("holds") else "DOES NOT HOLD"
            lines.append("- **%s** (%s). %s"
                         % (pid, mark, sch.PSA_PREMISE_PLAIN.get(pid, "")))
        valid = self.d.verdict == "ACCEPTED"
        result = ("Every premise holds, and every challenge that can be put "
                  "to them can be answered, so the system's explanation is "
                  "that the plan is **valid**." if valid else
                  "At least one challenge cannot be answered, so the system's "
                  "explanation is that the plan is **not valid**.")
        return (
            "**The Plan Summary Argument.**\n"
            "Conclusion. %s\n"
            "A premise is an assumption the conclusion depends on. If one did "
            "not hold, the conclusion would no longer be supported. This "
            "argument has eight.\n%s\n"
            "%s\n"
            "To test it, choose a premise below and put a critical question "
            "to the system."
            % (self._clean_text(s8.get("conclusion", "")), "\n".join(lines),
               result))

    def _justify(self, reply) -> str:
        record = reply.content["record"]
        meta = reply.content["meta"]
        node = reply.target
        ctx = self._context(node)
        idx = ctx["idx"]
        a = idx[0] if idx else None

        premise_ref = str(meta.get("s8_premise", "")).split(":")[0].strip()
        premise_plain = sch.PSA_PREMISE_PLAIN.get(premise_ref, "")
        scheme_id = (record.get("Defeated by")
                     or sch.first_scheme_id(meta.get("defeated_by", "")))
        name, claim = sch.SCHEMES.get(scheme_id, ("", ""))

        head = ("**The challenge is defeated.** %s was a challenge to premise "
                "%s of the Plan Summary Argument: %s"
                % (record["CQ"], premise_ref, premise_plain))
        claim = re.sub(r"^Claims ", "It claims ", claim)
        use = ("To answer it, the system uses the argument scheme **%s %s**. "
               "%s %s" % (scheme_id, name, claim, SCHEME_REMINDER))

        premises = record.get("Defeating premises") or []
        body = []
        for i, premise in enumerate(premises, 1):
            body.append("Premise %d. %s" % (i, self.premise_sentence(
                premise.get("label", ""), premise.get("detail", ""), ctx)))
        if not premises:
            body.append("Premise 1. %s"
                        % self._scheme_statement(record, a))
        body.append("Conclusion. %s" % self.conclusion_sentence(record, ctx))

        why = ("Why this answers the question. %s"
               % self._logic_text(meta.get("defeating_logic", ""),
                                  skip=(scheme_id,)))
        tail = ("So the challenge fails, and premise %s of the Plan Summary "
                "Argument still stands." % premise_ref)

        parts = [head, use, "\n".join(body), why, tail]
        other = self._different_subject(record, idx)
        if other is not None:
            parts.append(
                "Note. For this plan the system holds a single invariant "
                "check, and it was carried out on %s. That is the check shown "
                "here in answer to your question about %s."
                % (self.act(other), self.act(a)))
        text = "\n\n".join(parts)
        if re.search(r"revers", text, re.I):
            text += "\n\n" + self._reversal_note(ctx)
        return text

    def _reversal_note(self, ctx: dict) -> str:
        order = ctx.get("ord")
        if order:
            early, late = order
            return ("Note. Reversing the order of %s before %s means making "
                    "%s run first instead." % (self.act(early), self.act(late),
                                               self.short(late)))
        return "Note. " + REVERSAL_NOTE.strip("()")

    def _different_subject(self, record: dict, idx: List[int]) -> Optional[int]:
        """If an answer is about a different action from the one asked about.

        The framework builder keeps one invariant-maintenance instance (see the
        limitations in the cross-domain README), so in the payment workflow the
        answer to CQ2 on several actions is the check made on one of them.
        Showing it without saying so would read as an error to a participant,
        and hiding it would misdescribe the data, so it is stated.
        """
        if record.get("CQ") != "CQ2" or not idx:
            return None
        m = re.search(r"throughout (\w+)\.", record.get("Defeating conclusion", ""))
        if not m or m.group(1) not in self.index_of:
            return None
        subject = self.index_of[m.group(1)]
        return subject if subject != idx[0] else None

    def _logic_text(self, text: str, skip=()) -> str:
        """The framework's own account of why a scheme answers a question.

        It refers to the scheme's internal premise numbers, which would clash
        with the Premise 1, 2, 3 shown above it, so those references are
        removed. Scheme ids are given their names at first mention.
        """
        out = text or ""
        out = re.sub(r"\s*S\d defeats CQ\d via Premise \d and CQ\d via "
                     r"Premise \d, different premises answering different "
                     r"questions\.", "", out)
        out = re.sub(r"(S\d)'s Premise \d \(([^)]*)\)", r"\1 (\2)", out)
        out = re.sub(r"(S\d)'s Premise \d", r"\1", out)
        out = out.replace("individual S1 applicability certificates",
                          "individual certificates of applicability from S1")
        out = self._clean_text(out)
        return self._name_schemes(out, skip=skip)

    def _scheme_statement(self, record: dict, a: Optional[int]) -> str:
        """For answers whose data lists no premises, restate the detail."""
        detail = self._clean_text(record.get("Detail", ""))
        if record.get("CQ") == "CQ5" and a is not None:
            return ("Scheme %s establishes that reversing an order of actions "
                    "would violate a timing constraint, which shows that the "
                    "current schedule of %s respects the deadline."
                    % (self.sname(record.get("Defeated by", "")), self.act(a)))
        return cap(detail)

    def _concede(self, reply) -> str:
        record = reply.content["record"]
        idx = node_indices(reply.target)
        return ("**The challenge succeeds.** %s was put to %s and nothing "
                "defeats it, so the premise it challenges does not stand and "
                "the plan fails on this point.\n\n%s"
                % (record["CQ"], " and ".join(self.act(i) for i in idx),
                   self._clean_text(record.get("Detail", ""))))

    def _not_applicable(self, reply) -> str:
        record = reply.content["record"]
        idx = node_indices(reply.target)
        a = idx[0] if idx else None
        A = self.act(a)
        detail = (record.get("Detail") or "").strip()
        known = {
            "No over-all invariant for this action.":
                "%s has no condition that must stay true throughout its run."
                % A,
            "No enabling dependency for this action.":
                "No other action has to finish before %s can start." % A,
        }
        if detail in known:
            reason = known[detail]
        elif detail.startswith("No concurrent action runs during"):
            reason = ("No other action runs at the same time as %s, so "
                      "nothing can remove a condition it needs." % A)
        else:
            reason = self._clean_text(detail)
        return ("**This question does not apply here.** %s\n\nSo it raises no "
                "challenge to the Plan Summary Argument." % reason)

    def _ground(self, reply) -> str:
        premise = reply.content["premise"]
        index = reply.content.get("premise_index", 0)
        ctx = self._context(reply.target)
        holds = premise.get("holds")
        sentence = self.premise_sentence(premise.get("label", ""),
                                         premise.get("detail", ""), ctx)
        return (
            "**Premise %d.** %s\n\n"
            "This %s. It can be read straight off the state of the world "
            "worked out from the plan: the starting situation, plus the "
            "effects of every action that has run up to that moment. There is "
            "no further evidence behind it."
            % (index + 1, sentence, "holds" if holds else "does not hold"))

    def _reformulate(self, reply) -> str:
        record = reply.content.get("record")
        if not record:
            return ("Put more simply: the system checked every requirement the "
                    "plan has to meet, and reports whether each was met.")
        ctx = self._context(reply.target)
        idx = ctx["idx"]
        bullets = []
        for premise in record.get("Defeating premises") or []:
            bullets.append("- " + self.premise_sentence(
                premise.get("label", ""), premise.get("detail", ""), ctx))
        text = ("**Put more simply.** The question was: %s\n\n"
                % self.question(record["CQ"], idx))
        if bullets:
            text += "The answer rests on the following.\n" + "\n".join(bullets)
        else:
            text += self._clean_text(record.get("Detail", ""))
        return text

    # ------------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------------

    def closing_summary(self) -> str:
        o = self.d.outcome()
        valid = o["verdict"] == "ACCEPTED"
        grounded = o["premises_grounded"]
        return ("You raised %d of the %d critical questions available and "
                "asked the system to justify %d %s of its answers. Its "
                "explanation was that the plan is %s."
                % (o["cqs_challenged"], o["cqs_available"], grounded,
                   "premise" if grounded == 1 else "premises",
                   "valid" if valid else "not valid"))
