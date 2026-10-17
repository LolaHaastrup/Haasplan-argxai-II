"""
schemes.py
==========

Plain-language descriptions of the nine argument schemes, the eight premises of
the Plan Summary Argument, and a builder for the framework diagram.

The descriptions are presentation only. Nothing in the framework is derived
from this file; it exists so a participant who has never met argumentation
theory can follow the explanation without a glossary beside them.
"""

import re
from typing import Dict, List

#: Scheme id to (short name, what it claims).
SCHEMES: Dict[str, tuple] = {
    "S0": ("Replayed State",
           "Reconstructs what is true at every moment, from the starting "
           "situation and the effects of every action that has run so far."),
    "S1": ("Action Applicability",
           "Claims an action could legally run over its scheduled window, "
           "because its start conditions held and nothing removed what it "
           "needed while it ran."),
    "S2": ("Causal Goal Support",
           "Claims an action earns its place, because something it produces "
           "is either required by a later action or is part of the goal."),
    "S3": ("Temporal Feasibility",
           "Claims an action's timing works, because whatever enables it "
           "finishes first and its own window respects any deadline."),
    "S4": ("Concurrent Executability",
           "Claims two overlapping actions could each legally begin at the "
           "moment their windows start to overlap."),
    "S5": ("Resource and Concurrency Feasibility",
           "Claims two overlapping actions are safe together, because they "
           "hold different exclusive resources and neither destroys what the "
           "other needs."),
    "S6": ("Temporal Ordering Justification",
           "Claims an ordering between two actions is necessary, because "
           "reversing it would remove something the later action requires."),
    "S7": ("Invariant Maintenance Justification",
           "Claims a condition that must stay true throughout an action does "
           "stay true, and is not removed by anything running alongside it."),
    "S8": ("Plan Summary Argument",
           "The top-level argument. Its conclusion is that the plan as a "
           "whole is valid, and it rests on eight premises."),
}

#: How the pieces fit together, in the order a participant meets them. The
#: supervisor's correction: the premises of the Plan Summary Argument are
#: assumptions that support its conclusion. A premise is CHALLENGED by a
#: critical question, and an argument scheme is what the system uses to ANSWER
#: that challenge. A premise is not itself a scheme.
PSA_STRUCTURE = (
    "**The Plan Summary Argument has one conclusion and eight premises.** The "
    "conclusion is that the plan is valid. Each premise is an assumption that "
    "conclusion depends on. You can challenge a premise by putting a critical "
    "question to the system, and the system answers the challenge by using an "
    "argument scheme: a pattern of reasoning with its own premises and its own "
    "conclusion."
)

PREMISE_SCHEME_NOTE = (
    "The plan itself is not an argument. The Plan Summary Argument is, which "
    "is why the explanation is organised around it rather than around the "
    "actions of the plan."
)

#: What each premise of the Plan Summary Argument says, in words that stand on
#: their own. Keyed by premise id. These are paraphrases of the labels in the
#: data (for example "P2: every action applicable (S1)"), written for a reader
#: who has not met the terms. The data keeps its formal labels.
PSA_PREMISE_PLAIN: Dict[str, str] = {
    "P1": "What is true at every moment of the plan can be worked out from the "
          "starting situation and the effects of the actions so far.",
    "P2": "Every action could legally run at the time it is scheduled.",
    "P3": "Every action contributes something the plan needs, either to a "
          "later action or to the goal.",
    "P4": "The timing of every action works: whatever it depends on finishes "
          "first, and any deadline is met.",
    "P5": "Actions that run at the same time could each legally start when "
          "their times begin to overlap.",
    "P6": "Actions that run at the same time do not clash over an exclusive "
          "resource or over a condition the other needs.",
    "P7": "Every ordering of two actions in the plan is necessary: running "
          "them the other way round would break the plan.",
    "P8": "Every condition that has to stay true while an action runs does "
          "stay true.",
}

#: A short title for each premise, for buttons.
PSA_PREMISE_SHORT: Dict[str, str] = {
    "P1": "What is true at each moment",
    "P2": "Every action can run",
    "P3": "Every action is needed",
    "P4": "The timing works",
    "P5": "Overlapping actions can start",
    "P6": "Overlapping actions do not clash",
    "P7": "Every ordering is necessary",
    "P8": "Conditions stay true",
}

PSA_EXPLANATION = (
    "The system's explanation is built around a single top-level argument "
    "called the **Plan Summary Argument**. Its conclusion is that the plan is "
    "valid, and it rests on eight premises.\n\n"
    "Each premise can be challenged by a **critical question**. A critical "
    "question is a standard challenge to the kind of reasoning a premise "
    "relies on, so it applies wherever that reasoning is used rather than only "
    "to this plan. The system answers a challenge with an **argument "
    "scheme**. Where a scheme answers the question, the challenge is "
    "**defeated** and the premise stands. Where no scheme can answer it, the "
    "challenge **succeeds** and the plan fails on that point.\n\n"
    "The explanation is therefore not a score or a judgement call. It is "
    "whatever survives once every applicable challenge has been put."
)

#: What a scheme is, said once and repeated wherever a scheme first appears in
#: an answer, so that no answer depends on having read the landing page.
SCHEME_DEFINITION = (
    "An argument scheme is a pattern of reasoning. Every scheme lists "
    "premises, which are the assumptions it relies on, followed by a "
    "conclusion, which is what those premises establish together."
)


def premise_scheme(premise_label: str) -> str:
    """The scheme id named inside a premise label, for example S1.

    Premise labels are written by the extractor and already carry the scheme
    in brackets, so reading it back is safer than keeping a second mapping
    that could fall out of step.
    """
    match = re.search(r"\((S\d)\)", premise_label or "")
    return match.group(1) if match else ""


def premise_id(index: int) -> str:
    """P1 for the first premise, and so on."""
    return "P%d" % index


def cqs_for_premise(cq_meta: Dict[str, dict], pid: str) -> List[str]:
    """The critical questions that attack one premise of the summary argument.

    Read from each question's own record of which premise it attacks, in the
    order CQ1 to CQ9.
    """
    out = [cq for cq, meta in cq_meta.items()
           if str(meta.get("s8_premise", "")).split(":")[0].strip() == pid]
    return sorted(out, key=lambda c: int(c[2:]) if c[2:].isdigit() else 99)


def scheme_label(scheme_id: str) -> str:
    if scheme_id in SCHEMES:
        return f"{scheme_id} — {SCHEMES[scheme_id][0]}"
    return scheme_id


def first_scheme_id(text: str) -> str:
    """Pull the leading scheme id out of a CQ_META string like 'S1 - Action…'."""
    text = (text or "").strip()
    for candidate in SCHEMES:
        if text.startswith(candidate):
            return candidate
    return ""


def build_dot(cq_rows: List[dict], cq_meta: Dict[str, dict]) -> str:
    """Return a Graphviz DOT string for the framework, aggregated by CQ type.

    One node per critical question rather than per instance. A plan with
    forty CQ instances would be unreadable as a graph; aggregating to the
    nine question types shows the STRUCTURE, which is what the diagram is
    for, and the table underneath carries the per-instance counts.

    Rendered client-side by Streamlit, so no Graphviz binary is needed on the
    server.
    """
    outcomes: Dict[str, Dict[str, int]] = {}
    for row in cq_rows:
        bucket = outcomes.setdefault(row["CQ"], {})
        bucket[row["Outcome"]] = bucket.get(row["Outcome"], 0) + 1

    lines = [
        "digraph AF {",
        "  rankdir=BT;",
        "  bgcolor=transparent;",
        '  node [fontname="Helvetica", fontsize=10, style="filled,rounded", '
        'shape=box, penwidth=0.8];',
        '  edge [fontname="Helvetica", fontsize=8, penwidth=0.9];',
        '  PSA [label="PSA(P)\\nPlan Summary Argument", fillcolor="#0B2D8F", '
        'fontcolor="white", shape=box, penwidth=0];',
    ]

    attacked_schemes = set()
    defeating_schemes = set()

    for cq_id in sorted(cq_meta, key=lambda c: int(c[2:])):
        if cq_id not in outcomes:
            continue
        meta = cq_meta[cq_id]
        attacked = first_scheme_id(meta.get("attacks", ""))
        defeater = first_scheme_id(meta.get("defeated_by", ""))
        counts = outcomes[cq_id]
        succeeds = counts.get("succeeds", 0)

        # A critical question that succeeds is an unanswered attack, so it is
        # IN under the grounded labelling and the premise it attacks is OUT.
        if succeeds:
            fill, font = "#C0392B", "white"
            status = f"{succeeds} succeed"
        elif counts.get("defeated", 0):
            fill, font = "#E8F6EE", "#1E8449"
            status = f"{counts['defeated']} defeated"
        else:
            fill, font = "#F1F2F4", "#6B7280"
            status = "not applicable"

        lines.append(f'  {cq_id} [label="{cq_id}\\n{status}", '
                     f'fillcolor="{fill}", fontcolor="{font}"];')

        if attacked:
            attacked_schemes.add(attacked)
            lines.append(f'  {cq_id} -> {attacked} '
                         f'[label="attacks", color="#C0392B", '
                         f'fontcolor="#C0392B", arrowhead=vee];')
        if defeater and not succeeds:
            defeating_schemes.add(defeater)
            lines.append(f'  {defeater} -> {cq_id} '
                         f'[label="defeats", color="#1E8449", '
                         f'fontcolor="#1E8449", arrowhead=vee];')

    for scheme_id in sorted(attacked_schemes | defeating_schemes):
        short = SCHEMES.get(scheme_id, (scheme_id, ""))[0]
        lines.append(f'  {scheme_id} [label="{scheme_id}\\n{short}", '
                     f'fillcolor="#EAF0FA", fontcolor="#0B2D8F"];')

    for scheme_id in sorted(attacked_schemes):
        lines.append(f'  {scheme_id} -> PSA '
                     f'[label="supports", color="#6B7280", '
                     f'fontcolor="#6B7280", arrowhead=normal];')

    lines.append("}")
    return "\n".join(lines)



