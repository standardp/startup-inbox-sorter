from datetime import datetime, timedelta

_RAW = [
    ("Maya Chen", "maya@ledgerly.io", "Ledgerly — pre-seed round for AI bookkeeping", "Hi! I'm the co-founder of Ledgerly. We automate bookkeeping and invoice reconciliation for SMBs using LLMs. We're raising a $1.5M pre-seed and have $20k MRR. Deck attached."),
    ("Diego Ramírez", "diego@solarmesh.co", "SolarMesh: community solar for LatAm", "Hola Pia, we're building a platform that lets apartment buildings share rooftop solar energy and cut emissions. Pilot in Bogotá with 12 buildings. Would love 20 minutes."),
    ("Aisha Bello", "aisha@curepath.health", "Intro: CurePath (telehealth for chronic care)", "CurePath connects patients with chronic conditions to doctors via telehealth and remote monitoring. 3 hospital partners, raising seed."),
    ("Tom Becker", "tom@stackwatch.dev", "Launching StackWatch on Product Hunt today", "We're launching StackWatch, open source observability for Kubernetes developers. Our SDK sets up in 2 minutes. Would love your support!"),
    ("Lucía Torres", "lucia@aulaviva.edu.co", "AulaViva — learning platform for public schools", "AulaViva helps teachers in public schools personalize learning for students with an adaptive course engine. 40 schools onboarded. Raising pre-seed."),
    ("Ravi Patel", "ravi@shieldgrid.ai", "ShieldGrid: zero trust for mid-market", "ShieldGrid is a cybersecurity startup detecting identity threats and fraud for mid-market companies. SOC 2 ready. Series A in Q1."),
    ("Sofia Rossi", "sofia@freshroute.com", "FreshRoute monthly investor update — October", "Founder update: FreshRoute's last-mile delivery for grocery stores grew 32% MoM. Fleet now 140 vehicles. Hiring ops leads."),
    ("Kenji Watanabe", "kenji@nanofold.bio", "NanoFold — protein design for drug discovery", "We use machine learning to design proteins for therapeutics. Lab results validated on 3 targets. Raising $4M seed."),
    ("Emma Laurent", "emma@hivehq.work", "HiveHQ: onboarding for remote teams", "HiveHQ is an HR platform that automates employee onboarding for remote teams. 120 companies on the waitlist, launching beta next month."),
    ("Carlos Mendes", "carlos@chainpay.xyz", "ChainPay — stablecoin payroll", "ChainPay lets startups pay contractors worldwide in stablecoins with a non-custodial wallet. Built on blockchain rails, $2M in volume."),
    ("Nina Okafor", "nina@loopcart.shop", "LoopCart: checkout for D2C brands", "LoopCart is a one-click checkout for Shopify D2C brands. We increase conversion by 18%. Raising a seed round; would love feedback on our deck."),
    ("Liam O'Brien", "liam@nestly.homes", "Nestly — proptech for renters", "Nestly helps renters and landlords manage rental payments and maintenance. Operating in 3 cities, $40k MRR."),
    ("Hana Kim", "hana@botanica-robotics.com", "Botanica Robotics: farm robots", "We build autonomous robots and sensors for agriculture that monitor crops and reduce water usage 30%. Hardware pilots with 5 farms."),
    ("Mateo Silva", "mateo@beatdrop.fm", "BeatDrop — music creator platform", "BeatDrop is a community app for independent music creators to collaborate and stream. 50k monthly users."),
    ("Grace Liu", "grace@flowdesk.app", "Flowdesk: AI agents for customer support", "Flowdesk builds AI agents that resolve customer support tickets for B2B SaaS companies. Integrates with your CRM. Founder here, raising seed."),
    ("Omar Haddad", "omar@carbonledger.earth", "CarbonLedger — carbon accounting for SMEs", "CarbonLedger measures emissions and builds sustainability reports for small manufacturers. Accelerator alum, raising pre-seed."),
    ("Isabel García", "isabel@mentepaz.com", "MentePaz: mental health app in Spanish", "MentePaz is a mental health and wellness app for Spanish speakers with therapist chat. 10k users, raising seed."),
    ("Ben Carter", "ben@vaultkey.io", "VaultKey — encryption SDK for developers", "VaultKey is a developer API for end-to-end encryption. Security without the headache. 300 GitHub stars in week one."),
    ("Newsletter", "news@techdigest.com", "This week in tech: 10 stories", "Your weekly digest of tech news, funding rounds and product launches."),
    ("Priya Nair", "priya@tutorly.ai", "Tutorly — AI tutor for exam prep", "Tutorly is an AI tutor helping university students prepare for exams with personalized courses. 8k students, raising pre-seed."),
]


def sample_emails() -> list[dict]:
    now = datetime.now()
    out = []
    for i, (name, addr, subject, body) in enumerate(_RAW):
        out.append({
            "id": f"sample-{i}",
            "source": "sample",
            "sender_name": name,
            "sender_email": addr,
            "subject": subject,
            "snippet": body[:200],
            "body": body,
            "received_at": (now - timedelta(hours=7 * i + 1)).isoformat(),
        })
    return out
