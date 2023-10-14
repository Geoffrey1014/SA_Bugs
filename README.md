# Finding and Understanding Defects in Static Analyzers
## Abstract
Static analyzers are playing crucial roles in finding program bugs or vulnerabilities, and thus improving
software reliability. However, these analyzers often report with both false positives (FPs) and false negatives
(FNs) resulting from implementation flaws and design choices, which obstruct their practical applicability.
Detecting the defects of analyzers remains challenging since static analyzers usually lack clear specifications,
and the results obtained from different static analyzers may differ.
To overcome this challenge, this paper designs two types of oracles to find defects in static analyzers with
randomly generated programs. The first oracle is derived from dynamic execution results and the second
one leverages the program states reasoned by the static analyzers. To evaluate the effectiveness of these two
oracles, we built a testing framework to perform a testing campaign on three state-of-the-art static analyzers:
Clang Static Analyzer (CSA), GCC Static Analyzer (GSA), and Pinpoint. We found 38 unique defects in these
analyzers, 28 of which have been confirmed or fixed by the developer. We conducted a comprehensive case
study on the found defects followed by several insights and lessons learned for improving static analyzers

