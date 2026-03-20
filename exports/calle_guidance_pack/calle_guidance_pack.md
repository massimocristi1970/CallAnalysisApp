# Calle AI Guidance Pack

This pack summarises the language, terms, and signal types currently used in CallAnalysisApp for positive scoring, vulnerability detection, and unhappy-customer detection.

Generated: 2026-03-20T18:38:03.933411+00:00

## 1. Call-Type Category Mapping

- **Customer Service**: Customer Understanding, Fair Treatment, Resolution & Support
- **Collections**: Customer Understanding, Fair Treatment, Vulnerability Handling, Financial Difficulty, Resolution & Support
- **Sales**: Customer Understanding, Fair Treatment, Resolution & Support
- **Support**: Customer Understanding, Fair Treatment, Resolution & Support

## 2. Positive / Desired Agent Language

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
  - learning difficulties
  - someone helps me
  - I'm not sure what you mean
  - this is all very confusing
  - I need someone to help me understand
  - so you're happy with that payment
  - okay so this is your final payment
  - are you happy we've got your payment
  - are you happy with that
  - i'll send you the payment schedule via email
  - ... plus 117 more phrases in the JSON/CSV export

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
  - i do need to just make you aware
  - that default now goes on hold
  - as long as you stick to the payment schedule
  - that default will not be registered
  - find out a bit more what's happening on your side
  - it would be something you would be able to afford
  - i'm going to take that late fee off
  - i don't want to put you into a payment plan where you're at detriment
  - where you don't have enough to buy food
  - if you're confident and happy that you can afford
  - ... plus 87 more phrases in the JSON/CSV export

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
  - had ADHD
  - Because you were going through some difficulty
  - I don't want you to enter into something that isn't sustainable
  - No, you're not under any pressure whatsoever
  - Okay, let's see where we're up to
  - That's okay. Don't worry
  - That will work and it's safe to do
  - We'll accommodate whichever works best for you
  - so, you've got some breathing room
  - I know what it's like
  - ... plus 23 more phrases in the JSON/CSV export

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
  - do you mind me asking what those financial difficulties are
  - how much extra are you paying
  - not able to make any payment not even a small payment
  - having a look at your financials
  - the change in your circumstances
  - your credit commitment is that still
  - your food and basic essentials
  - do you have any other credit commitments
  - do you have any other active loans
  - are you able to make a small payment
  - ... plus 102 more phrases in the JSON/CSV export

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
  - i set that payment schedule up
  - you're more than welcome to send an email
  - what i can do for you is
  - are you happy with monthly payment or weekly payments
  - so you looking at us restarting your payment schedule
  - we are giving you the grace period
  - let's look at setting a new payment arrangement
  - i will remove the late charge
  - so if we do it over multiple payments
  - let me just put that in place for you
  - ... plus 105 more phrases in the JSON/CSV export

## 3. Vulnerability Signals

### acute_distress_or_safeguarding

- Why it matters: Potential immediate welfare, safeguarding, or severe distress risk.
- Recommended response style: Prioritise safety, de-escalate, avoid pressure, and follow safeguarding or escalation procedures immediately.
- Example terms: suicide, harassment, scam, police, sectioned, domestic violence, psychosis, abused, abusive, coercion, manipulated, mental breakdown, restraining order, refuge, feel like giving up, breaking point

### mental_health_or_cognitive

- Why it matters: Customer may have reduced resilience, reduced understanding, or need a slower and more supportive approach.
- Recommended response style: Use simple language, repeat key information, check understanding, and ask whether any support or reasonable adjustments would help.
- Example terms: vulnerable, lacks understanding, mental health, depression, anxiety, stress, bipolar, PTSD, ADHD, autism, therapist, disorientated, medication, overwhelmed, mental health crisis, stressed

### health_bereavement_or_life_event

- Why it matters: Customer circumstances may be materially affected by illness, bereavement, injury, or major life disruption.
- Recommended response style: Acknowledge the situation, avoid unnecessary probing, offer flexibility, and reduce pressure while still explaining options clearly.
- Example terms: terminal, cancer, injury, death, diagnosis, long term sick, rehabilitation, chronic pain, mobility issues, funeral, grieving, child unwell, bereavement, illness, surgery

### financial_hardship_and_basic_needs

- Why it matters: Customer may be unable to maintain payments without harming essential living costs or priority commitments.
- Recommended response style: Explore affordability first, discuss priority bills, consider smaller payments or holds, and avoid unaffordable commitments.
- Example terms: can't afford, no money left, skip meals, heating or eating, financial difficulties, job loss, foodbank, overdrawn, no money, no income, rent arrears, overcommitted, financial difficulty, financial trouble, between jobs, priority bills, priority debts, zero disposable income, negative budget, energy arrears
- Additional terms available in export: 7

### housing_or_stability_risk

- Why it matters: Customer may be experiencing housing instability or other major life disruption that affects their ability to engage normally.
- Recommended response style: Use a supportive and practical approach, avoid pressure, and focus on stability and realistic next steps.
- Example terms: homeless, sofa surfing, eviction, temporary accommodation, zero hours contract, casual work, gig economy

### other_relevant_vulnerability_or_hardship_terms

- Why it matters: Additional terms already treated as risk or support indicators by the app.
- Recommended response style: Treat as a cue to assess whether a more supportive or lower-pressure response is needed.
- Example terms: complaint, threaten, i've had enough, multiple payment option offering, plan implementation, spare money utilization, online payment facilitation, default notice, court action, bailiff, debt collector, enforcement, legal action, bankruptcy, choosing between, struggling, unable to pay, late payment, refund, collection
- Additional terms available in export: 99

## 4. Unhappy Customer Signals

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
  - i wish to complain
  - i am disappointed
  - i'm disappointed
  - i'm really disappointed
  - you're not helping
  - ... plus 56 more phrases in the JSON/CSV export

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
  - i'll be taking this further
  - i'll go to the ombudsman
  - trading standards
  - i'll contact
  - i'll be contacting
  - ... plus 2 more phrases in the JSON/CSV export

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
  - it won't let me
  - i can't
  - i couldn't
  - i tried
  - i've tried
  - ... plus 24 more phrases in the JSON/CSV export

## 5. Recommended Response Principles

- **When vulnerability is indicated**: Slow the conversation down, check understanding, reduce pressure, and offer support or flexibility before focusing on payment or process.
- **When the customer sounds unhappy or frustrated**: Acknowledge the emotion first, avoid sounding scripted or defensive, then explain the fix or escalation path clearly.
- **When affordability or hardship is indicated**: Prioritise sustainable outcomes, explore income and expenditure, and avoid setting commitments that could worsen the customer’s position.
- **When explaining actions or next steps**: Use short plain-English explanations, confirm dates and amounts, and check whether the customer wants anything repeated or sent in writing.

## 6. Source Notes

- Positive language and call-type mapping come from `config.yaml`.
- Unhappy-customer signals come from `customer_sentiment.py` pattern matching.
- The recommended response principles are a cleaned summary derived from the app's current scoring and signal logic.
