# Calle AI Guidance Pack

This pack summarises the language, terms, and signal types currently used in CallAnalysisApp for positive scoring, vulnerability detection, and unhappy-customer detection.

Generated: 2026-03-23T16:03:13.257016+00:00
Pack version: 2.0

## 1. Purpose and Boundaries

- Intended audience: project manager, AI vendor implementation team, conversation designers, and QA or risk reviewers.
- Integration model: offline handoff pack only. This export gives the vendor the signal definitions and guidance at a point in time, but not live access to the app.
- Use this pack as operational guidance input rather than as a compliance policy or rigid script library.
- Where vulnerability, safeguarding, or severe distress is detected, supportive handling should take precedence over collections pressure.

## 2. Implementation Summary

- Literal phrases: use as example wording or direct match seeds, not as the only accepted wording.
- Regex patterns: keep as pattern-based rules rather than flattening them into exact strings.
- Priority field: only vulnerability keywords carry direct source priority; other rows should be prioritised by severity and local policy.
- Low-confidence or unmatched calls should be logged and reviewed rather than answered too confidently.

## 3. Delivery Checklist

- Load the JSON pack first and preserve the provided category and signal-group labels.
- Keep regex-pattern rows as pattern rules and literal rows as examples or seed phrases.
- Apply stronger escalation and lower-pressure handling when vulnerability or acute distress is detected.
- Separate advisory guidance from hard routing or suppression rules in the vendor platform.
- Test against sample call snippets before enabling the rules on live traffic.
- Log low-confidence, unmatched, and false-positive interactions for the next pack refresh.

## 4. Call-Type Category Mapping

- **Customer Service**: Customer Understanding, Fair Treatment, Resolution & Support
- **Collections**: Customer Understanding, Fair Treatment, Vulnerability Handling, Financial Difficulty, Resolution & Support
- **Sales**: Customer Understanding, Fair Treatment, Resolution & Support
- **Support**: Customer Understanding, Fair Treatment, Resolution & Support

## 5. Positive / Desired Agent Language

### Customer Understanding

- Why it matters: Shows the agent is checking understanding, slowing down where needed, and making information easier for the customer to follow.
- Recommended response style: Use plain language, confirm understanding, invite questions, and summarise dates, amounts, and next steps clearly.
- Example phrases:
  - do you understand
  - let me explain
  - does that make sense
  - is that clear
  - just to clarify
  - i'll walk you through
  - happy to explain again
  - take your time to understand
  - feel free to ask questions
  - would you like me to repeat
  - explain it simply
  - easy to understand
  - clear explanation
  - any questions so far
  - let me break that down
  - i can rephrase that for you
  - can you explain that again
  - i'm confused
  - I don't understand
  - I have memory problems
  - ... plus 127 more phrases in the JSON/CSV export

### Fair Treatment

- Why it matters: Shows the customer is being treated respectfully and without unnecessary pressure, especially where affordability or vulnerability may be relevant.
- Recommended response style: Be calm, non-judgmental, transparent about consequences, and avoid pushing the customer into unaffordable or unsuitable actions.
- Example phrases:
  - we're here to help
  - take your time
  - you have options
  - we won't pressure you
  - we want what's best for you
  - we'll support you
  - no obligation
  - your decision
  - you're in control
  - we'll do our best
  - treat you fairly
  - understand your situation
  - i understand this is a challenging time for you
  - I can see how difficult this must be
  - I appreciate you sharing this with me
  - That sounds really tough
  - I want to make sure I understand correctly
  - how much longer do you think
  - how many days you were off work
  - is there any reason for your payments not coming out
  - ... plus 97 more phrases in the JSON/CSV export

### Vulnerability Handling

- Why it matters: Shows the agent has recognised or responded appropriately to signs of distress, health issues, bereavement, reduced understanding, or other vulnerability indicators.
- Recommended response style: Slow down, acknowledge the situation, reduce pressure, offer support or flexibility where available, and check what help or adjustments would make things easier.
- Example phrases:
  - can I ask if you're okay
  - do you need any support
  - we support mental health
  - are you getting help
  - do you have a medical condition
  - we can pause the account
  - we can send a breathing space form
  - you don't have to explain
  - we understand vulnerability
  - difficult situation
  - i understand this is a challenging time for you
  - what is happening on your side
  - having somebody understand the situation that you are in
  - don't worry yourself
  - no need to stretch yourself
  - i'm glad you're on the road to recovery
  - are you currently behind in any of your priority bills?
  - Any future payments that would have been set up are now cancelled
  - my deepest condolences
  - I do understand that you did say
  - ... plus 33 more phrases in the JSON/CSV export

### Financial Difficulty

- Why it matters: Shows the agent is exploring affordability and priority commitments rather than simply chasing payment.
- Recommended response style: Focus on affordability, income and expenditure, priority bills, sustainable arrangements, and practical options such as holds, reduced payments, or reviews.
- Example phrases:
  - we can set up a plan
  - we can work something out
  - affordable repayment
  - can pause payments
  - need income and expenditure
  - repayment flexibility
  - let's look at options
  - freeze interest
  - we'll be fair
  - a lot to pay for
  - waiting on redundancy payment
  - we'll review your income & expenditure
  - i do have some concerns as we are not getting any payments
  - what unexpected bills are you getting
  - just to confirm you're still getting the salary
  - to confirm is your rent still
  - other outgoings are they still about
  - how much they've increased by
  - do you contribute towards food
  - is there any reason why you can't make this month's payment
  - ... plus 112 more phrases in the JSON/CSV export

### Resolution & Support

- Why it matters: Shows the agent is moving the call forward with clear actions, ownership, and next steps.
- Recommended response style: Explain what will happen next, confirm actions taken, send confirmation where possible, and check whether the customer needs anything else.
- Example phrases:
  - we'll investigate
  - we'll raise a complaint
  - we can escalate this
  - here's what we'll do
  - next steps
  - i've raised that for you
  - we'll send confirmation
  - thank you for confirming
  - anything else I can help you with
  - see what we can do for you
  - we need to look at you making smaller payments
  - what if we set up smaller payments
  - how much can you put towards your loan
  - what amount would you be able to afford to pay
  - set something up that is affordable for you
  - is there anything else i can help you with on my end
  - let me do that for you
  - just reset that up for you
  - let's have a look and see what we can do
  - if i reset your payment schedule
  - ... plus 115 more phrases in the JSON/CSV export

## 6. Vulnerability Signals

### acute_distress_or_safeguarding

- Why it matters: Potential immediate welfare, safeguarding, or severe distress risk.
- Recommended response style: Prioritise safety, de-escalate, avoid pressure, and follow safeguarding or escalation procedures immediately.
- Example terms: suicide, harassment, scam, police, sectioned, domestic violence, psychosis, abused, abusive, coercion, manipulated, mental breakdown, restraining order, refuge, feel like giving up
- Additional terms available in export: 1

### mental_health_or_cognitive

- Why it matters: Customer may have reduced resilience, reduced understanding, or need a slower and more supportive approach.
- Recommended response style: Use simple language, repeat key information, check understanding, and ask whether any support or reasonable adjustments would help.
- Example terms: vulnerable, lacks understanding, mental health, depression, anxiety, stress, bipolar, PTSD, ADHD, autism, therapist, disorientated, medication, overwhelmed, mental health crisis
- Additional terms available in export: 1

### health_bereavement_or_life_event

- Why it matters: Customer circumstances may be materially affected by illness, bereavement, injury, or major life disruption.
- Recommended response style: Acknowledge the situation, avoid unnecessary probing, offer flexibility, and reduce pressure while still explaining options clearly.
- Example terms: terminal, cancer, injury, death, diagnosis, long term sick, rehabilitation, chronic pain, mobility issues, funeral, grieving, child unwell, bereavement, illness, surgery

### financial_hardship_and_basic_needs

- Why it matters: Customer may be unable to maintain payments without harming essential living costs or priority commitments.
- Recommended response style: Explore affordability first, discuss priority bills, consider smaller payments or holds, and avoid unaffordable commitments.
- Example terms: can't afford, no money left, skip meals, heating or eating, financial difficulties, job loss, foodbank, overdrawn, no money, no income, rent arrears, overcommitted, financial difficulty, financial trouble, between jobs
- Additional terms available in export: 12

### housing_or_stability_risk

- Why it matters: Customer may be experiencing housing instability or other major life disruption that affects their ability to engage normally.
- Recommended response style: Use a supportive and practical approach, avoid pressure, and focus on stability and realistic next steps.
- Example terms: homeless, sofa surfing, eviction, temporary accommodation, zero hours contract, casual work, gig economy

### other_relevant_vulnerability_or_hardship_terms

- Why it matters: Additional terms already treated as risk or support indicators by the app.
- Recommended response style: Treat as a cue to assess whether a more supportive or lower-pressure response is needed.
- Example terms: complaint, threaten, i've had enough, multiple payment option offering, plan implementation, spare money utilization, online payment facilitation, default notice, court action, bailiff, debt collector, enforcement, legal action, bankruptcy, choosing between
- Additional terms available in export: 104

## 7. Unhappy Customer Signals

### frustration_and_complaints

- Why it matters: Signals dissatisfaction, loss of trust, or an elevated risk of complaint if the interaction is not handled well.
- Recommended response style: Acknowledge the frustration, avoid defensiveness, take ownership of next steps, and explain what will happen clearly.
- Example phrases:
  - i am unhappy
  - i'm unhappy
  - i am frustrated
  - i'm frustrated
  - i am angry
  - i'm angry
  - i'm furious
  - i'm livid
  - i'm fuming
  - i'm not happy
  - i'm not pleased
  - i'm not impressed
  - i'm not satisfied
  - i have a complaint
  - i want to complain
  - ... plus 61 more phrases in the JSON/CSV export

### escalation_requests

- Why it matters: Shows the customer believes normal resolution has failed or wants the matter reviewed by someone more senior.
- Recommended response style: Stay calm, explain the escalation path clearly, capture the issue accurately, and avoid obstructing legitimate escalation.
- Example phrases:
  - i need to speak to (?:a|the)
  - can i speak to (?:a|your)
  - put me through to
  - i want to escalate
  - i want to make a complaint
  - i need a manager
  - i want a manager
  - i demand to speak
  - get me a supervisor
  - let me speak to someone else
  - someone more senior
  - your supervisor
  - your manager
  - complaints department
  - i want to take this further
  - ... plus 7 more phrases in the JSON/CSV export

### urgency_signals

- Why it matters: Shows time pressure and may indicate heightened emotional risk or practical consequences if delayed.
- Recommended response style: Set realistic expectations, prioritise immediate clarifications, and be explicit about timelines and what can be done now.
- Example phrases:
  - this is urgent
  - i need this sorted
  - i need this resolved
  - i need this fixed
  - as soon as possible
  - asap
  - right away
  - immediately
  - straight away
  - today
  - by the end of
  - i can't wait
  - time sensitive
  - critical

### skepticism_and_doubt

- Why it matters: Shows the customer may not trust the explanation they are being given.
- Recommended response style: Use transparent explanations, avoid jargon, and restate the reason, evidence, and next step in simple terms.
- Example phrases:
  - are you sure
  - is that right
  - that doesn't sound right
  - that can't be right
  - i don't think that's
  - i was told something different
  - that's not what i was told
  - i don't believe
  - really\?
  - seriously\?
  - you're joking

### confusion_and_problems

- Why it matters: Shows the customer may not understand what is happening or may be struggling to complete the required action.
- Recommended response style: Break the task into smaller steps, check understanding, and avoid overwhelming the customer with too much information at once.
- Example phrases:
  - my problem is
  - i'm having trouble
  - i am having trouble
  - i'm having issues
  - i'm having difficulty
  - i don't understand
  - i can't understand
  - i'm confused
  - i'm a bit confused
  - i'm not sure
  - i don't know why
  - this isn't working
  - this is not working
  - it's not working
  - it doesn't work
  - ... plus 29 more phrases in the JSON/CSV export

## 8. Recommended Response Principles

- **When vulnerability is indicated**: Slow the conversation down, check understanding, reduce pressure, and offer support or flexibility before focusing on payment or process.
- **When the customer sounds unhappy or frustrated**: Acknowledge the emotion first, avoid sounding scripted or defensive, then explain the fix or escalation path clearly.
- **When affordability or hardship is indicated**: Prioritise sustainable outcomes, explore income and expenditure, and avoid setting commitments that could worsen the customer's position.
- **When explaining actions or next steps**: Use short plain-English explanations, confirm dates and amounts, and check whether the customer wants anything repeated or sent in writing.

## 9. Change Control Guidance

- **Detection thresholds and escalation handling**: Owner: AI vendor implementation lead plus your operational owner. Approval needed: Yes. Why: These changes can alter how vulnerable, distressed, or unhappy customers are handled.
- **Customer-facing wording and scripting**: Owner: Conversation design owner. Approval needed: Yes. Why: Changes may affect fairness, clarity, or pressure in live interactions.
- **Taxonomy, labels, and routing metadata**: Owner: Vendor product or configuration team. Approval needed: Usually. Why: Lower-risk operational tuning, but still affects reporting and call flows.
- **Analytics dashboards and internal tagging only**: Owner: Vendor analytics team. Approval needed: Usually not. Why: Safe to tune if it does not change live customer outcomes or suppression logic.

## 10. Sample Test Scenarios

### CALLE-001

- Call type: Collections
- Example customer utterance: I lost my job, I can barely cover rent, and I do not understand what happens next.
- Expected detection: financial_hardship_and_basic_needs, confusion_and_problems
- Expected agent behaviour: Slow down, check understanding, explore affordability before asking for commitment, and explain next steps in plain English.
- Escalation expectation: Review for supportive treatment and affordability handling.

### CALLE-002

- Call type: Customer Service
- Example customer utterance: I want to make a complaint and speak to a manager today.
- Expected detection: frustration_and_complaints, escalation_requests, urgency_signals
- Expected agent behaviour: Acknowledge the frustration, explain the complaint path clearly, and avoid sounding defensive or obstructive.
- Escalation expectation: Follow complaints or supervisor-routing process.

### CALLE-003

- Call type: Collections
- Example customer utterance: My partner passed away and I am struggling to keep on top of everything.
- Expected detection: health_bereavement_or_life_event
- Expected agent behaviour: Acknowledge the bereavement, reduce pressure, keep questions minimal, and offer flexible next steps.
- Escalation expectation: Apply bereavement or vulnerability handling path where available.

### CALLE-004

- Call type: Collections
- Example customer utterance: Are you sure that is right? I was told something different last week.
- Expected detection: skepticism_and_doubt
- Expected agent behaviour: Restate the explanation plainly, clarify the evidence or reason, and confirm what happens next.
- Escalation expectation: No automatic escalation, but monitor for unresolved distrust.

### CALLE-005

- Call type: Collections
- Example customer utterance: I feel like giving up. I cannot do this anymore.
- Expected detection: acute_distress_or_safeguarding
- Expected agent behaviour: Prioritise immediate safety and safeguarding steps, stop standard collections pressure, and route urgently.
- Escalation expectation: Immediate safeguarding escalation.

## 11. Source Notes

- Positive language and call-type mapping come from `config.yaml`.
- Unhappy-customer signals come from `customer_sentiment.py` pattern matching.
- The recommended response principles are a cleaned summary derived from the app's current scoring and signal logic.
