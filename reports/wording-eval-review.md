# Wording eval v0.1: spot-check (E18)

640 never-seen questions (640 examples) from eval v0.2, each asked with three wordings of the same options. Per source: banking77 80, jailbreak_classification 80, bias_in_bios 80, contract_nli 80, ethics_commonsense 80, fin_tweets_topic 80, fin_tweets_sentiment 80, arxiv_field 80.

**Check: does each rewording mean the same as the original, and is it still clearly different from the other options?** Every rewording used in the eval is listed below.

## banking77

| Original | Description | Paraphrase |
|---|---|---|
| Refund not showing up | The user reports that a previously requested refund has not appeared in their account. | Missing refund |
| activate my card | The inquiry concerns how to enable or start using a new card that was received. | Enable card |
| age limit | The question asks about the minimum age required to create an account or obtain a card. | Age requirement |
| apple pay or google pay | The user wants to know whether Apple Pay or Google Pay can be used with their card. | Digital wallet support |
| atm support | The request seeks information on which ATMs can be used for cash withdrawals. | ATM compatibility |
| automatic top up | The user asks how to set up automatic top‑ups for their account balance. | Auto top‑up |
| balance not updated after bank transfer | The complaint is that the account balance did not change after a bank transfer was made. | Balance unchanged after transfer |
| balance not updated after cheque or cash deposit | The user notes that their balance has not updated after depositing cash or a cheque. | Balance unchanged after deposit |
| beneficiary not allowed | The question states that a chosen beneficiary cannot be added or used for transfers. | Beneficiary blocked |
| card about to expire | The inquiry indicates that the current card is nearing its expiration date and needs replacement. | Expiring card |
| card acceptance | The user asks where the card can be used for purchases or services worldwide. | Card acceptance locations |
| card arrival | The question concerns the arrival status of a newly ordered physical card. | Card arrival status |
| card delivery estimate | The user wants an estimate of how long delivery will take for a pending card shipment. | Delivery timeframe |
| card linking | The request is about linking an existing card to the app or another service. | Connect card |
| card not working | The user reports that their card does not function for any transaction attempts. | Card malfunction |
| card payment fee charged | The complaint involves a fee being charged for a card payment that the user believes is incorrect. | Unexpected payment fee |
| card payment not recognised | The user does not recognize a particular card transaction and suspects it may be fraudulent. | unrecognized payment |
| card payment wrong exchange rate | The issue is that a card payment was processed using an exchange rate that the user finds inaccurate. | Wrong FX rate |
| card swallowed | The user reports that an ATM has retained their card, preventing its retrieval. | Card captured |
| cash withdrawal charge | The user wants information about a cash withdrawal fee that was applied. | question on withdrawal charge |
| cash withdrawal not recognised | The user states that a cash withdrawal appears on their account that they did not perform. | unknown cash withdrawal |
| change pin | The user wants instructions on updating or resetting their card PIN. | PIN change request |
| compromised card | The user suspects that their card details are at risk and need protection. | compromised card concern |
| contactless not working | The user cannot complete a transaction using the contactless feature of their card. | contactless not functional |
| country support | The user wants to know if they can use the service in a particular nation. | country availability question |
| declined card payment | The user experiences a rejection of a card transaction and wants to know why. | declined card purchase |
| declined cash withdrawal | The user could not obtain cash because the ATM refused the transaction. | cash withdrawal rejection |
| declined transfer | The user asks why their money transfer was not approved and was rejected. | declined money transfer |
| direct debit payment not recognised | The user cannot locate a direct debit on their statement and wants clarification. | unrecognised direct debit |
| disposable card limits | The user wants to know the limits for creating or using disposable virtual cards. | disposable card caps |
| edit personal details | The request is to modify personal information such as name or address. | Edit personal data |
| exchange charge | The user wants to know the charge applied when exchanging currencies. | Exchange fee query |
| exchange rate | The inquiry is about the exchange rate used for a currency conversion. | Rate of exchange question |
| exchange via app | The user asks how to perform a currency exchange using the mobile application. | App exchange procedure |
| extra charge on statement | The user sees an additional charge on their statement and wants clarification. | Extra statement charge |
| failed transfer | The user reports a transfer that failed to complete. | transfer failure |
| fiat currency support | The question asks which fiat currencies are supported for holding or spending. | Supported fiat currencies |
| get disposable virtual card | The user wants to obtain a disposable virtual card for temporary use. | Get disposable card |
| get physical card | The request is to order or receive a physical payment card. | Physical card request |
| getting spare card | The user wants a replacement card because their current one is missing or damaged. | spare card request |
| getting virtual card | The user is asking for a digital card that can be used online or in-app. | virtual card request |
| lost or stolen card | The user reports that their card has been lost or stolen and needs assistance. | card loss or theft |
| lost or stolen phone | The user indicates their phone is lost or stolen and seeks help with account access. | phone loss or theft |
| order physical card | The user wants to order a new physical card to be mailed to them. | physical card order |
| passcode forgotten | The user cannot remember their passcode and needs to reset it. | forgotten passcode |
| pending card payment | The user has a card payment that is still pending and wants to know its status. | card payment pending |
| pending cash withdrawal | The user has an ATM cash withdrawal that is still pending in the system. | cash withdrawal pending |
| pending top up | The user reports a top‑up that has not yet completed and is awaiting confirmation. | top‑up pending |
| pending transfer | The user has an incoming or outgoing transfer that remains pending. | transfer pending |
| pin blocked | The user’s PIN is blocked after too many incorrect attempts and needs unlocking. | blocked PIN |
| receiving money | The user wants information about how to receive money from another party. | receiving funds |
| request refund | The user wants a refund for a transaction they made. | request reimbursement |
| reverted card payment? | The user’s card payment was reversed or reverted and they need clarification. | reverted payment |
| supported cards and currencies | The user inquires about which cards and currencies are supported for transactions. | supported cards/currencies |
| terminate account | The user wishes to close their account permanently. | close account |
| top up by bank transfer charge | The user asks about fees for topping up via a bank transfer. | bank transfer top‑up charge |
| top up by card charge | The user asks about fees for topping up using a debit or credit card. | card top‑up charge |
| top up by cash or cheque | The user wants to know the costs for topping up with cash or a cheque. | cash/cheque top‑up charge |
| top up failed | The user reports that their attempt to top up was unsuccessful. | top‑up failure |
| top up limits | The request concerns the limit on how much can be topped up. | top‑up cap |
| top up reverted | The question states that the added money disappeared after initially appearing. | reinstated top‑up |
| topping up by card | The user wants instructions for funding the account with a payment card. | top‑up via card |
| transaction charged twice | The complaint notes that a single purchase appeared as two separate payments. | double billing |
| transfer fee charged | The request concerns an unexpected cost taken for sending funds. | fee on transfer |
| transfer into account | The question is about depositing funds directly into the account. | funds into account |
| transfer not received by recipient | The complaint states the transfer was not delivered to the beneficiary. | transfer not delivered |
| transfer timing | The user wants to know the expected timing for a money transfer. | transfer speed |
| unable to verify identity | The user cannot complete the identity verification process. | identity check fails |
| verify my identity | The request asks for instructions on how to verify their identity for the service. | identity verification steps |
| verify source of funds | The user seeks to confirm the origin of the funds they are using for a transaction. | source of funds verification |
| verify top up | The user wants to confirm that a top‑up has been verified successfully. | top‑up verification status |
| virtual card not working | The problem described is that a virtual card cannot be used for transactions. | virtual card failure |
| visa or mastercard | The user wants to know whether they can use Visa, Mastercard, or both with the service. | card network support |
| why verify identity | The question asks why the service requires the user to go through identity verification. | reason for identity check |
| wrong amount of cash received | The user reports receiving an incorrect amount of cash from an ATM withdrawal. | cash amount incorrect |
| wrong exchange rate for cash withdrawal | The complaint concerns an exchange rate applied to a cash withdrawal that seems wrong. | bad cash‑withdrawal rate |

## jailbreak_classification

| Original | Description | Paraphrase |
|---|---|---|
| no | no, the prompt does not attempt to bypass the assistant’s safety constraints. | not an evasion attempt |
| yes | yes, the prompt tries to manipulate the assistant into ignoring its safeguards. | attempts to jailbreak |

## bias_in_bios

| Original | Description | Paraphrase |
|---|---|---|
| DJ | The person’s job is to select, blend, and cue tracks in clubs or events. | Club spinner |
| accountant | The individual handles accounts, tax filings, and budgeting for businesses or clients. | Money manager |
| architect | This person develops architectural concepts, drafts blueprints, and coordinates with engineers. | Structure planner |
| attorney | This person practices law, drafts contracts, and negotiates settlements for others. | Law practitioner |
| chiropractor | This person provides chiropractic care, manipulates joints, and advises on posture. | Back specialist |
| comedian | This person crafts comedic material, appears on stage, and engages crowds with laughter. | Comic performer |
| composer | This person composes melodies, orchestrates works, and produces original music content. | Songwriter |
| dentist | This person provides dental care, extracts teeth, and creates restorative dental work. | Oral surgeon |
| dietitian | This person assesses dietary needs, recommends foods, and educates clients about nutrition. | Food consultant |
| filmmaker | This person writes scripts, manages production, and coordinates crew to bring stories to screen. | Film maker |
| interior designer | They are employed as an interior designer. | Space decorator |
| journalist | Their occupation is journalist. | News reporter |
| model | The person works as a model, showcasing clothing and products in photo shoots and runway shows. | Fashion showcase |
| nurse | The individual works professionally as a nurse. | Healthcare caregiver |
| painter | Their job is that of a painter. | Artistic painter |
| paralegal | They hold the position of paralegal. | Legal assistant |
| pastor | The person serves in the role of pastor. | Spiritual leader |
| personal trainer | Their employment is as a personal trainer. | Fitness coach |
| photographer | They work professionally as a photographer. | Image capture artist |
| physician | Their occupation is physician. | Medical doctor |
| poet | The individual’s profession is writing poetry as a creative writer. | verse author |
| professor | The person holds an academic position teaching at a university level. | college educator |
| psychologist | The person works as a psychologist, diagnosing conditions and delivering psychological treatment. | clinical psychologist |
| rapper | The individual creates rap songs, writes lyrics, and stages concerts for listeners. | rap performer |
| software engineer | The person designs, writes, and maintains computer programs as a software engineer. | code developer |
| surgeon | This individual is a surgeon, performing operative procedures to treat medical conditions. | operative physician |
| teacher | The person instructs students in a classroom setting as a teacher. | lesson facilitator |
| yoga teacher | The individual leads physical and breathing exercises as a yoga instructor. | mind‑body trainer |

## contract_nli

| Original | Description | Paraphrase |
|---|---|---|
| no | no, the excerpt fails to confirm the assertion. | assertion not present |
| yes | The excerpt clearly affirms the statement, indicating the claim is true. | clearly affirmed |

## ethics_commonsense

| Original | Description | Paraphrase |
|---|---|---|
| no | no, the narrator's action is not clearly morally wrong according to ordinary standards. | not immoral |
| yes | yes, the narrator clearly acted wrongly by ordinary moral standards. | clearly unethical |

## fin_tweets_topic

| Original | Description | Paraphrase |
|---|---|---|
| Analyst Update | The article provides an update from an analyst regarding market outlook or stock assessment. | Analyst insight |
| Company / Product News | The piece announces a new product launch or a company's recent corporate development. | Company news |
| Currencies | The content focuses on foreign exchange movements, rates, or currency market analysis. | FX update |
| Dividend | The text reports on dividend declarations, payouts, or changes to shareholder returns. | Dividend news |
| Earnings | The story discusses a company's quarterly or annual earnings results and related metrics. | Earnings report |
| Energy / Oil | The item discusses developments in the energy sector, oil prices, or related commodities. | Energy/Oil update |
| Fed / Central Banks | The text addresses actions, statements, or policy shifts by the Federal Reserve or central banks. | Fed/central bank |
| Financials | The piece pertains to financial institutions, banking results, or sector-specific financial news. | Financial sector |
| General News / Opinion | The content offers a general commentary, editorial view, or broad market opinion piece. | Opinion piece |
| Gold / Metals / Materials | The article highlights gold, precious metals, or broader material commodity price movements. | Gold/Metals |
| IPO | The text announces a new initial public offering, listing details, or IPO pricing information. | IPO announcement |
| Legal / Regulation | The piece addresses legal issues, regulatory changes, or compliance matters affecting markets. | Legal/regulatory news |
| M&A / Investments | The piece reports on mergers, acquisitions, or investment transactions between companies. | M&A activity |
| Macro | The article discusses macro‑economic trends, indicators, or broad economic policy impacts. | Macro outlook |
| Markets | The news reports on stock market indices, trading volumes, or overall market sentiment. | Market snapshot |
| Personnel Change | The text details a change in personnel, such as a new executive hire or departure. | Staff change |
| Politics | The article covers political events, policy decisions, or government actions influencing finance. | Political news |
| Stock Commentary | The piece provides commentary on a specific stock’s fundamentals, valuation, or analyst opinion. | Stock analysis |
| Stock Movement | The content reports on a particular stock’s price movement, gains, losses, or volatility. | Stock price |
| Treasuries / Corporate Debt | The article addresses treasury yields, bond market trends, or corporate debt issuance updates. | Bond market |

## fin_tweets_sentiment

| Original | Description | Paraphrase |
|---|---|---|
| bearish | It signals pessimism about the market, implying a downward trend ahead. | downward bias |
| bullish | The message expresses optimism, predicting that asset values will rise shortly. | positive outlook |
| neutral | The text remains balanced, presenting no clear bias toward price direction. | no clear stance |

## arxiv_field

| Original | Description | Paraphrase |
|---|---|---|
| astrophysics | The paper's main focus lies within the study of stars, galaxies, or cosmology. | Astronomy research |
| computer science | The work primarily deals with algorithms, data structures, software, or theoretical computing concepts. | Computing discipline |
| condensed matter physics | The document concentrates on solid‑state phenomena, material properties, or low‑temperature physics. | Solid‑state physics |
| economics | The study examines markets, financial systems, economic theory, or policy analysis. | Economic research |
| electrical engineering and systems science | The content addresses circuits, signal processing, control systems, or hardware engineering topics. | Electrical engineering |
| general relativity and quantum cosmology | The manuscript explores spacetime curvature, black holes, or the universe's large‑scale structure. | Relativity & cosmology |
| high energy physics | The paper investigates particle accelerators, fundamental forces, or high‑energy collider experiments. | Particle physics |
| mathematics | The research presents new theorems, proofs, or abstract mathematical structures. | Pure mathematics |
| nonlinear sciences | The work studies chaotic systems, complex networks, or interdisciplinary dynamic models. | Complex systems |
| nuclear physics | The article focuses on nuclear reactions, decay processes, or atomic nucleus properties. | Nuclear science |
| physics (applied, optics, fluids and other) | The paper addresses applied physics topics such as optics, fluid dynamics, or instrumentation. | Applied physics |
| quantitative biology | The paper is in the quantitative biology domain. | Bio‑quantitative |
| quantitative finance | The research centers on mathematical models of financial markets, risk, or investment strategies. | financial modeling |
| quantum physics | The research examines quantum states, entanglement, or other phenomena at atomic scales. | Quantum mechanics |
| statistics | The paper presents statistical theory, inference methods, or data analysis techniques. | Statistical study |

## One question, three ways

- **wording:original**: Is this prompt an attempt to jailbreak an AI assistant? → yes / no
- **wording:description**: Is this prompt an attempt to jailbreak an AI assistant? → yes, the prompt tries to manipulate the assistant into ignoring its safeguards. / no, the prompt does not attempt to bypass the assistant’s safety constraints.
- **wording:paraphrase**: Is this prompt an attempt to jailbreak an AI assistant? → attempts to jailbreak / not an evasion attempt
