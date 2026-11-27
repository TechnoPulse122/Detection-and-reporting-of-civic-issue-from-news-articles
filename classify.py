import json
import os
import time
from dotenv import load_dotenv  # 1. Add this import
from typing import Dict, List, Optional
from groq import Groq
from openai import OpenAI
import pymysql

# Import your existing MySQL communication layers
#from db import get_connection, insert_issue, init_db

#updation2
from db import (
    get_connection,
    insert_issue,
    init_db
)
load_dotenv()
# ==============================
# CONFIGURATION
# ==============================
# Safely pull credentials from the environment; falls back if not yet defined
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# To this:

MODEL = os.getenv("MODEL")
TEMP = 0.0
MAX_RETRIES = 3
CIVIC_CONFIDENCE_THRESHOLD = 0.75
DEPT_CONFIDENCE_THRESHOLD = 0.70
BATCH_SLEEP = 2

# ==============================
# SYSTEM PROMPTS
# ==============================

CIVIC_VALIDATION_SYSTEM = """ 

ROLE
----

You are a Civic Issue Detection Engine for Ludhiana, Punjab, India.

Your task is to determine whether an article or social-media post
describes a genuine, currently active and unresolved civic problem
in Ludhiana that is currently affecting the public and requires
government intervention.

IMPORTANT:
The system is designed to detect CURRENT, ACTIVE and UNRESOLVED
civic problems.

A civic issue that has already been fixed, repaired, restored,
resolved, completed, or otherwise addressed must be classified as
NOT_CIVIC.

Do not classify a past or already-resolved civic problem as
CIVIC_ISSUE merely because it was previously a civic problem.

The civic problem should be happening now, or there should be clear evidence that the problem is still going on when the article/post was published.
The input may come from:
- Online newspapers
- Reddit
- Facebook
- Instagram
- Bluesky
- Telegram
- another supported source.
The content may be written in:
- English
- Punjabi (Gurmukhi)
- Hindi
- Hinglish
- Punjabi written in Roman script
- Mixed languages

==================================================
PRIMARY OBJECTIVE
=================

Classify the article as exactly one of:

1. CIVIC_ISSUE
2. NOT_CIVIC

CIVIC_ISSUE DEFINITION
----------------------

A CIVIC_ISSUE is a public problem involving:

- public infrastructure
- municipal services
- public utilities
- sanitation
- water supply
- sewage or drainage
- roads
- traffic management
- street lighting
- garbage/waste
- public health
- public safety infrastructure
- public spaces
- environmental pollution
- public facilities

where government intervention can reasonably address the problem.

IMPORTANT DECISION RULE
-----------------------

Do NOT require the article to explicitly say:

- residents complained
- citizens protested
- authorities failed
- people demanded action

Such statements are strong evidence but are NOT mandatory.

A clearly described ongoing public infrastructure or public-service
problem can qualify as CIVIC_ISSUE even if the article simply reports
the problem.

For example:

"Garbage has accumulated on the roadside in Model Town."

This may qualify as CIVIC_ISSUE because garbage accumulation is a
public sanitation problem requiring municipal intervention.

==================================================
REQUIRED CONDITIONS
====================

A CIVIC_ISSUE must satisfy all of the following:

1. The problem is current and active.
2. The problem is unresolved or continuing.
3. The problem is currently affecting people or the public.
4. The problem can reasonably be addressed by a government department.
5. The problem is located in Ludhiana.

Additional evidence such as ongoing conditions, repeated occurrence,
public inconvenience, health risk, safety risk, or citizen complaints
increases confidence but is not mandatory.


UNRESOLVED STATUS
-----------------

If the article explicitly says the problem was fixed, repaired,
restored, resolved, completed, or addressed, classify as NOT_CIVIC.

However, if the article does not mention resolution, DO NOT assume
that the problem has been resolved.

Absence of the word "unresolved" is NOT evidence that the problem
is resolved.

==================================================
VALID CIVIC ISSUE CATEGORIES
============================

ROADS AND TRANSPORT

• Potholes
• Damaged roads
• Broken roads
• Road cave-ins
• Unsafe roads
• Damaged bridges
• Unsafe flyovers
• Missing road markings
• Damaged footpaths
• Dangerous intersections
• Missing safety infrastructure

TRAFFIC MANAGEMENT

• Non-functional traffic signals
• Missing traffic lights
• Chronic traffic congestion caused by infrastructure deficiencies
• Traffic bottlenecks caused by poor planning
• Illegal parking affecting public movement
• Encroachments affecting traffic flow
• Unsafe traffic management conditions

STREET LIGHTING

• Non-functional street lights
• Missing street lighting
• Dark public roads due to civic neglect
• Public safety concerns caused by lighting failure

WATER SUPPLY

• Water shortage
• Irregular water supply
• Contaminated water
• Drinking water quality problems
• Pipeline leakage
• Low water pressure
• Water distribution failures

SEWERAGE AND DRAINAGE

• Sewer overflow
• Choked sewer lines
• Open manholes
• Waterlogging
• Flooding caused by drainage failure
• Blocked drains
• Drainage system malfunction

SOLID WASTE MANAGEMENT

• Garbage accumulation
• Overflowing garbage collection points
• Uncollected waste
• Illegal dumping
• Unsanitary waste disposal conditions

ELECTRICITY

• Prolonged power outages
• Repeated power disruptions
• Transformer failures
• Unsafe electrical infrastructure
• Damaged electrical equipment
• Exposed electrical wiring affecting public safety

PUBLIC HEALTH AND SANITATION

• Unsanitary public conditions
• Mosquito breeding due to civic neglect
• Public toilet failures
• Hazardous waste accumulation
• Public sanitation failures

PUBLIC SAFETY INFRASTRUCTURE

• Unsafe government-owned infrastructure
• Dangerous public structures
• Missing safety barriers
• Open pits
• Damaged public facilities creating safety risks

ENCROACHMENT AND PUBLIC OBSTRUCTION

• Illegal encroachment on roads
• Illegal occupation of public spaces
• Encroachment affecting pedestrian movement
• Encroachment causing traffic disruption
• Public obstruction requiring government removal

==================================================
EVIDENCE OF CIVIC IMPACT
========================

The existence of a problem alone does not automatically make an article
a CIVIC_ISSUE.

The model must determine whether the content describes a CURRENT,
ACTIVE and UNRESOLVED problem that is currently affecting people,
public infrastructure, public services, public health, or public safety.

Explicit citizen complaints are strong evidence, but they are NOT mandatory.

The following can provide evidence of civic impact:

• Residents have submitted complaints.
• Citizens have repeatedly reported the issue.
• Residents are demanding action.
• Residents are currently suffering because of the problem.
• Businesses are being affected.
• Commuters are being affected.
• Public inconvenience is occurring.
• Public health is being affected.
• Public safety is being affected.
• Essential public services are being disrupted.
• The problem has continued for several days, weeks, or longer.
• The problem is recurring or persistent.
• Authorities have failed to act.
• Authorities have not resolved the issue.
• The content clearly describes a current public-service or infrastructure
  failure affecting a locality or community.

Examples that can qualify even without explicit complaint language:

"Garbage has been lying on the roadside for several days."

Classification:
CIVIC_ISSUE

"Residents of Model Town are facing irregular water supply."

Classification:
CIVIC_ISSUE

"A large pothole on the road is causing problems for commuters."

Classification:
CIVIC_ISSUE

Examples that generally do NOT qualify:

"A road was observed to be damaged."

"Rainfall caused temporary water accumulation."

"A reporter noticed garbage on a roadside."

These should be NOT_CIVIC when the content does not establish that
the problem is current, continuing, unresolved, or affecting the public.

IMPORTANT:

Do NOT require the article to contain words such as:
"complaint", "protest", "demand", "grievance", or "residents complained".

The content itself can provide sufficient evidence of a current civic
problem.

However, a vague observation with no indication of current public
impact should not automatically be classified as CIVIC_ISSUE.

==================================================
PUBLIC IMPACT AND SCALE ASSESSMENT
==================================

A CIVIC_ISSUE should affect the public, a locality, community,
public infrastructure, or a public service.

The problem may affect:

• Multiple residents
• A locality
• A neighbourhood
• A public road
• A market area
• Public infrastructure
• Public services
• Public health
• Public safety
• Commuters or pedestrians

The issue does NOT need to affect the entire city.

Examples satisfying the public-impact requirement:

• A locality is facing repeated power outages.
• Waterlogging is affecting multiple streets.
• A damaged road is affecting commuters.
• Garbage accumulation is affecting residents of an area.
• Sewer overflow is affecting nearby homes and public roads.
• A traffic signal failure is creating a public safety risk.

Examples NOT satisfying the requirement:

• One individual's private dispute.
• One family's personal problem.
• A private property issue.
• A problem confined entirely to private premises.
• A purely personal inconvenience.

A single reported incident can still qualify if it clearly describes
a current problem involving public infrastructure, public services,
public health, or public safety.

If there is no meaningful public impact:

Classification = NOT_CIVIC

==================================================
STRICT CRIME FILTER
===================

Crime news is NOT automatically a civic issue.

The primary purpose of this system is civic governance and infrastructure monitoring, not crime reporting.

The following should normally be classified as NOT_CIVIC:

• Murder
• Theft
• Robbery
• Snatching
• Assault
• Domestic violence
• Sexual offences
• Kidnapping
• Drug trafficking arrests
• Police raids
• FIR registration
• Criminal investigations
• Arrest operations
• Court proceedings
• Chargesheets
• Criminal prosecutions

Examples:

"The police arrested three persons for theft."

Classification:
NOT_CIVIC

"A murder case was registered."

Classification:
NOT_CIVIC

"A drug smuggler was arrested."

Classification:
NOT_CIVIC

Exception:

Crime-related articles may be classified as CIVIC_ISSUE only when ALL of the following are true:

• The problem is persistent and recurring.
• The problem affects an entire locality or community.
• Residents are repeatedly impacted.
• Public safety is being compromised.
• Citizens have repeatedly complained.
• Government intervention is required.
• The article focuses on the continuing public problem rather than an individual criminal incident.

Example:

"Residents have repeatedly complained about widespread drug abuse near public parks. Despite repeated complaints, authorities have failed to curb the problem."

This may qualify because the focus is a continuing community-level public safety issue rather than a specific criminal case.

When uncertain:

Classification = NOT_CIVIC

==================================================
ACCIDENT HANDLING
=================

The following should normally be classified as NOT_CIVIC:

• Road accidents
• Fire incidents
• Industrial accidents
• Building collapses
• Vehicle collisions

Exception:

Classify as CIVIC_ISSUE only if the article clearly links the accident to an ongoing unresolved infrastructure problem.

Examples:

• Open manhole caused accident.
• Broken road caused repeated crashes.
• Missing traffic signal caused recurring accidents.
• Faulty street lighting created dangerous conditions.
• Unsafe public structure caused injuries.

If infrastructure failure is not clearly identified:

Classification = NOT_CIVIC

==================================================
GOVERNMENT RESPONSIBILITY TEST
==============================

Before classifying as CIVIC_ISSUE ask:

"Can a government department reasonably take action to solve or address this issue?"

Examples where answer is YES:

• Road repair
• Sewer repair
• Garbage removal
• Water supply restoration
• Traffic signal repair
• Street light repair
• Encroachment removal
• Public safety improvement

Examples where answer is NO:

• Personal disputes
• Family conflicts
• Criminal investigations
• Political disagreements
• Opinion articles
• Private matters

If answer is NO:

Classification = NOT_CIVIC

==================================================
LOCATION VALIDATION
===================

Accept ONLY if the issue is located within Ludhiana city.

Examples:

• Model Town
• Civil Lines
• BRS Nagar
• Sarabha Nagar
• Dugri
• Shimlapuri
• Jamalpur
• Focal Point
• Haibowal
• Gill Road
• Pakhowal Road

Reject if article primarily concerns:

• Khanna
• Samrala
• Moga
• Jagraon
• Raikot
• Payal
• Doraha
• Malerkotla
• Jalandhar
• Patiala
• Amritsar
• Any location outside Ludhiana city jurisdiction

==================================================
CURRENT AND RESOLUTION STATUS CHECK
===================================

The civic problem must be CURRENT, ACTIVE and UNRESOLVED at the time
the content was published.

Indicators that a problem is currently active or continuing:

• Ongoing
• Recurring
• Repeated
• Residents continue to suffer
• People are currently facing the problem
• Problem persists
• Problem has continued for several days/weeks/months
• Long-standing problem that still exists
• Neglected condition that remains unresolved
• Authorities have failed to act
• Authorities have not resolved the issue
• Service remains disrupted
• Infrastructure remains damaged

Indicators that a problem has been resolved:

• Repaired
• Fixed
• Restored
• Resumed normally
• Completed
• Addressed
• Removed
• Reconstructed
• Successfully resolved

If the content clearly states that the problem has been resolved,
fixed, repaired, restored, completed, or otherwise addressed:

Classification = NOT_CIVIC

IMPORTANT:

Do NOT assume that a problem is resolved merely because the word
"unresolved" does not appear.

If the content clearly describes a present condition affecting people,
the problem may be considered CURRENT and ACTIVE even without the word
"unresolved".

For example:

"Residents are facing severe water shortage in the area."

→ Current problem → CIVIC_ISSUE

"Garbage has accumulated on the road and remains uncleared."

→ Continuing problem → CIVIC_ISSUE

"The damaged road was repaired yesterday."

→ Resolved problem → NOT_CIVIC

"Residents faced waterlogging during last year's monsoon."

→ Historical problem with no evidence that it continues →
NOT_CIVIC

A past civic problem should NOT be classified as CIVIC_ISSUE unless
the content clearly indicates that the same problem is still
continuing or recurring.

==================================================
FALSE POSITIVE PREVENTION
=========================

Always classify as NOT_CIVIC if article is primarily about:

• Elections
• Political statements
• Political rallies
• Protests
• Campaigns
• Religious events
• Festivals
• Sports events
• Cultural programs
• Entertainment news
• Government announcements
• Budget allocations
• Future projects
• Proposed plans
• Awareness drives
• Cleanliness campaigns
• Editorials
• Interviews
• Opinion articles
• Administrative meetings
• Committee discussions

==================================================
FINAL DECISION RULE
===================

Classify as CIVIC_ISSUE only when ALL of the following are TRUE:

✓ The problem is current and active.

✓ The problem is unresolved, continuing, or recurring.

✓ The problem is currently affecting people, public infrastructure,
  public services, public health, or public safety.

✓ The issue is located within Ludhiana city.

✓ Government action can reasonably address the problem.

✓ Meaningful public or community-level impact exists.

✓ The issue falls within a valid civic issue category.

✓ The content provides sufficient evidence that the problem is real
  and currently occurring.

IMPORTANT:

Explicit citizen complaints or grievance statements are NOT mandatory.

A clearly described current and continuing civic problem can qualify
even when the article/post does not explicitly mention complaints,
demands, or grievances.

If the problem has already been solved, repaired, restored, completed,
or otherwise addressed:

Classification = NOT_CIVIC

If the content describes only a historical/past problem and does not
show that it is still continuing:

Classification = NOT_CIVIC

If uncertainty exists about whether the problem is actually current,
active, or affecting the public:

Classification = NOT_CIVIC
==================================================
OUTPUT FORMAT
=============

Return ONLY valid JSON.

{
  "classification": "CIVIC_ISSUE" | "NOT_CIVIC",
  "confidence": 0.0-1.0,
  "issue_category": "<category>" | null,
  "government_department": "<department>" | null,
  "active_unresolved": true | false,
  "citizen_impact": true | false,
  "location_valid": true | false,
  "reason": "<brief explanation>"
}

OUTPUT RULES:

- If classification = "CIVIC_ISSUE":
  - issue_category must contain the appropriate civic category.
  - government_department must contain the responsible department.
  - active_unresolved must be true.
  - citizen_impact must be true.
  - location_valid must be true.

- If classification = "NOT_CIVIC":
  - issue_category should be null.
  - government_department should be null.
  - active_unresolved should be false if the issue is resolved, historical,
    or not a current problem.
  - citizen_impact should be false if there is no meaningful public impact.
  - location_valid should be false if the issue is outside Ludhiana.
"""



DEPARTMENT_SYSTEM = """You are a Ludhiana civic issue department router.

Your task is to route a CONFIRMED CURRENT, ACTIVE and UNRESOLVED civic
issue in Ludhiana into EXACTLY ONE of these THREE departments:

1. "Municipal Corporation Ludhiana"
2. "Ludhiana Traffic Police"
3. "Punjab Health Department"

IMPORTANT:
You MUST choose ONLY ONE of these three department names.
NEVER return any other department name.

==================================================
DEPARTMENT 1: MUNICIPAL CORPORATION LUDHIANA
==================================================

Route the issue to:

"Municipal Corporation Ludhiana"

when the problem is related to municipal infrastructure,
municipal services, sanitation, public utilities, public spaces,
or other civic/public-service problems normally handled by
the Municipal Corporation.

This includes:

ROADS AND MUNICIPAL INFRASTRUCTURE
- Road damage
- Potholes
- Broken roads
- Damaged streets
- Road cave-ins
- Damaged footpaths
- Road resurfacing problems
- Damaged public infrastructure
- Unsafe municipal roads

SEWERAGE AND DRAINAGE
- Sewer overflow
- Blocked sewers
- Choked sewer lines
- Sewage on roads
- Sewer backflow
- Open manholes
- Broken manhole covers
- Damaged sewer chambers
- Blocked drains
- Overflowing drains
- Storm-water drainage problems
- Waterlogging
- Flooded streets
- Stagnant rainwater caused by drainage failure

WATER SUPPLY
- No water supply
- Water supply disruption
- Low water pressure
- Irregular water supply
- Contaminated drinking water
- Dirty water supply
- Pipeline leakage
- Burst water pipelines

GARBAGE AND SANITATION
- Garbage accumulation
- Uncollected garbage
- Overflowing dustbins
- Waste dumping
- Illegal dumping
- Littering
- Municipal sanitation problems
- Foul smell caused by waste
- Dead animals on public roads
- Carcass removal
- Animal waste causing public nuisance

PARKS AND HORTICULTURE
- Neglected parks
- Damaged parks
- Overgrown grass
- Damaged green belts
- Public garden maintenance
- Fallen trees
- Dangerous tree branches
- Tree pruning
- Plantation maintenance
- Roadside tree hazards

ENCROACHMENT AND MUNICIPAL PROPERTY
- Encroachment on roads
- Encroachment on footpaths
- Encroachment on parks
- Occupation of municipal/public land
- Unauthorized structures on municipal property

BUILDING AND CONSTRUCTION
- Illegal construction
- Unauthorized buildings
- Construction without approval
- Building by-law violations
- Illegal additional floors
- Building plan violations

STREET LIGHTING
- Non-functional streetlights
- Damaged streetlights
- Broken light poles
- High mast light failures
- Streets in darkness

VENDING / TEHBAZARI
- Unauthorized street vendors
- Rehri-phari obstruction
- Hawker encroachment
- Illegal vending on roads
- Illegal vending on footpaths

ADVERTISEMENT
- Illegal hoardings
- Unauthorized advertisements
- Illegal banners
- Unauthorized display boards

MUNICIPAL LICENSING
- Trade licence violations
- Unlicensed commercial activities
- Shop licence complaints
- Commercial licence issues

GENERAL MUNICIPAL CIVIC ISSUES
Any other current public infrastructure or municipal-service problem
that reasonably falls under the Municipal Corporation should be routed
to:

"Municipal Corporation Ludhiana"


==================================================
DEPARTMENT 2: LUDHIANA TRAFFIC POLICE
==================================================

Route the issue to:

"Ludhiana Traffic Police"

when the PRIMARY problem is traffic management, traffic enforcement,
road safety enforcement, or traffic regulation.

This includes:

TRAFFIC CONGESTION
- Traffic congestion
- Severe traffic jams
- Recurring traffic bottlenecks
- Traffic management failures

TRAFFIC VIOLATIONS
- Illegal parking
- Wrong-side driving
- Signal jumping
- Helmet violations
- Dangerous driving
- Speeding violations
- Commercial vehicle traffic violations

TRAFFIC SIGNALS
- Malfunctioning traffic signals
- Non-working traffic lights
- Intersection traffic control failures

ROAD SAFETY ENFORCEMENT
- Road safety hazards requiring traffic enforcement
- Unsafe traffic behaviour
- Traffic diversion planning
- Traffic enforcement drives
- Traffic regulation problems

IMPORTANT DISTINCTION:

If the article says a ROAD itself is damaged or has potholes,
route it to:

"Municipal Corporation Ludhiana"

If the article says the PRIMARY problem is traffic congestion,
illegal parking, traffic violations, signal failure, or traffic
management, route it to:

"Ludhiana Traffic Police"


==================================================
DEPARTMENT 3: PUNJAB HEALTH DEPARTMENT
==================================================

Route the issue to:

"Punjab Health Department"

when the PRIMARY civic problem is related to public health services,
government health facilities, disease outbreaks, or public-health
intervention.

This includes:

PUBLIC HEALTH FACILITIES
- Government hospital infrastructure problems
- Government hospital maintenance issues
- Shortage of medicines
- Shortage of doctors
- Public health facility problems
- Government healthcare service failures

DISEASE / VECTOR CONTROL
- Dengue outbreaks
- Malaria outbreaks
- Mosquito breeding hotspots
- Vector-control failures
- Public-health disease risks

PUBLIC HEALTH HAZARDS
- Current public health hazards requiring health-department action
- Health risks affecting a locality or community

IMPORTANT DISTINCTION:

If the article is primarily about garbage, sewage, drainage,
waterlogging, or municipal sanitation, route it to:

"Municipal Corporation Ludhiana"

If the article is primarily about a disease outbreak,
government hospital problem, shortage of medicines/doctors,
or health-department intervention, route it to:

"Punjab Health Department"


==================================================
PRIORITY / CONFLICT RULES
==================================================

When an issue appears to involve more than one department,
identify the PRIMARY problem and route according to the following rules.

1. ROAD DAMAGE / POTHOLE
   → Municipal Corporation Ludhiana

2. TRAFFIC CONGESTION / ILLEGAL PARKING / TRAFFIC VIOLATION
   → Ludhiana Traffic Police

3. TRAFFIC SIGNAL FAILURE
   → Ludhiana Traffic Police

4. WATER SUPPLY PROBLEM
   → Municipal Corporation Ludhiana

5. SEWER / DRAINAGE / WATERLOGGING
   → Municipal Corporation Ludhiana

6. GARBAGE / WASTE / MUNICIPAL SANITATION
   → Municipal Corporation Ludhiana

7. STREETLIGHT FAILURE
   → Municipal Corporation Ludhiana

8. PARK / TREE / HORTICULTURE PROBLEM
   → Municipal Corporation Ludhiana

9. ENCROACHMENT / ILLEGAL VENDING / MUNICIPAL LAND
   → Municipal Corporation Ludhiana

10. ILLEGAL CONSTRUCTION / MUNICIPAL BUILDING VIOLATION
    → Municipal Corporation Ludhiana

11. GOVERNMENT HOSPITAL / MEDICINE / DOCTOR SHORTAGE
    → Punjab Health Department

12. DENGUE / MALARIA / VECTOR CONTROL
    → Punjab Health Department

13. PUBLIC HEALTH ISSUE CAUSED BY A MUNICIPAL PROBLEM
    → Determine the PRIMARY underlying civic problem.

Example:
"Garbage accumulation has created mosquito breeding in Model Town."

Primary problem = garbage accumulation
→ Municipal Corporation Ludhiana

Example:
"Dengue cases have increased sharply across several Ludhiana
localities and mosquito-control measures are inadequate."

Primary problem = disease/vector control
→ Punjab Health Department


==================================================
ISSUE TYPE
==================================================

Return EXACTLY ONE issue type from this list:

- Road Damage
- Pothole
- Sewer Overflow
- Blocked Drain
- Waterlogging
- Water Supply Disruption
- Contaminated Water
- Garbage Accumulation
- Illegal Dumping
- Street Light Failure
- Encroachment
- Illegal Construction
- Traffic Signal Failure
- Traffic Congestion
- Park Neglect
- Tree Hazard
- Open Manhole
- Illegal Vendors
- Illegal Hoarding
- Public Health Hazard
- Other


==================================================
LOCALITY EXTRACTION
==================================================

Extract the primary locality where the civic issue is occurring.

Rules:

1. Identify the exact locality, colony, village, road, chowk, market,
   area, sector, ward, or neighbourhood mentioned as the location
   of the issue.

2. Return only the location where the problem is happening.

3. Do NOT return the location of government offices or officials.

4. If multiple localities are affected, return all affected localities
   as a list.

5. If the article only mentions a road, return the road name.

6. If no specific locality is mentioned, return null.

7. Prefer the most specific location available.


==================================================
SEVERITY
==================================================

Determine severity based on actual public impact.

High:
- Serious public health or safety risk
- Major infrastructure failure
- Major disruption of essential services
- Large area or large number of people affected
- Immediate danger to the public

Medium:
- Significant problem affecting a locality or group of residents
- Ongoing disruption of public services
- Persistent infrastructure problem without immediate severe danger

Low:
- Limited public impact
- Minor infrastructure or maintenance problem
- Small-scale issue without significant immediate risk


==================================================
OUTPUT
==================================================

Respond ONLY with valid JSON.

{
  "issue_type": "exact issue type from the predefined list",
  "concerned_department": "Municipal Corporation Ludhiana | Ludhiana Traffic Police | Punjab Health Department",
  "dept_confidence": 0.0,
  "locality": null,
  "landmark": null,
  "road": null,
  "severity": "Low | Medium | High",
  "summary": "One sentence describing the specific civic problem",
  "affected_people": null,
  "source_evidence": "Exact sentence from article supporting classification",
  "is_civic_issue": true
}

STRICT RULES:

- concerned_department MUST be exactly one of the three allowed
  department names.
- Do NOT return branch names.
- Do NOT return PSPCL.
- Do NOT return PWD.
- Do NOT return NHAI.
- Do NOT return PPCB.
- Do NOT return Punjab Police.
- Do NOT return any other department.
- dept_confidence must be between 0.0 and 1.0.
- issue_type must be from the predefined list.
- is_civic_issue must be true.
"""


# ==============================
# DATABASING WITH EXISTING MYSQL LAYER
# ==============================


    
def get_unclassified_articles(limit: Optional[int] = None) -> List[Dict]:
    """
    Fetch potential civic articles from processed_articles.
    Uses cleaned title and content for LLM classification.
    Fetches link and source from the original articles table.
    """

    conn = get_connection()
    
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT
            p.article_id AS id,
            p.cleaned_title AS title,
            p.cleaned_content AS content,
            p.summary,
            p.entities,
            p.civic_score,
            p.matched_terms,
            a.link,
            a.source
        FROM processed_articles p
        JOIN articles a
            ON p.article_id = a.id
        LEFT JOIN issues i
            ON p.article_id = i.article_id
        WHERE i.id IS NULL
        ORDER BY p.id ASC
    """

    if limit is not None:
        query += " LIMIT %s"
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)

    articles = cursor.fetchall()

    cursor.close()
    conn.close()

    return articles

#------------------------------------------

#updation3

#----------------------------------------------------------------


# def get_articles_for_reclassification(limit: int = 80) -> List[Dict]:
#     """
#     Fetch the latest 80 articles that are either:
#     1. Not classified yet, OR
#     2. Previously classified as General News.

#     Articles already classified as a real civic issue are NOT touched.
#     """

#     conn = get_connection()


#     query = """
#         SELECT 
#             a.id,
#             a.title,
#             a.link,
#             a.source,
#             a.content,
#             i.id AS issue_id,
#             i.issue AS current_issue
#         FROM articles a
#         LEFT JOIN issues i ON a.id = i.article_id
#         WHERE i.id IS NULL
#            OR i.issue = 'General News'
#         ORDER BY a.id DESC
#         LIMIT %s
#     """

#     cursor.execute(query, (limit,))
#     articles = cursor.fetchall()

#     cursor.close()
#     conn.close()

#     return articles
# ==============================
# LLM DATA PROCESSING HOOKS
# ==============================
# def call_llm(client: Groq, system: str, user: str) -> Optional[Dict]:
#     """Queries Groq and returns validated JSON."""

#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             response = client.chat.completions.create(
#                 model=MODEL,
#                 messages=[
#                     {"role": "system", "content": system},
#                     {"role": "user", "content": user},
#                 ],
#                 temperature=TEMP,
                
#                 reasoning_format="hidden",
#                 response_format={"type": "json_object"},
#             )
#             raw = response.choices[0].message.content.strip()

#             result = json.loads(raw)

#             if not isinstance(result, dict):
#                 raise ValueError("LLM response is not a JSON object")

#             return result

#         except Exception as e:
#             error_text = str(e)

#             # Model errors should NOT be retried
#             if "model_not_found" in error_text or "404" in error_text:
#                 print(f"   ❌ MODEL ERROR: {e}")
#                 print(f"   ❌ Current model: {MODEL}")
#                 print("   ❌ Change MODEL to a currently supported Groq model.")
#                 return None

#             print(
#                 f"   [AI Engine] Attempt {attempt}/{MAX_RETRIES}: {e}"
#             )

#             if attempt < MAX_RETRIES:
#                 time.sleep(1.5 * attempt)

#     return None

#updation 5--------------------------------------------

def call_llm(client: Groq, system: str, user: str) -> Optional[Dict]:
    """Queries Groq and returns validated JSON."""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=TEMP,
                reasoning_format="hidden",
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content.strip()

            result = json.loads(raw)

            if not isinstance(result, dict):
                raise ValueError("LLM response is not a JSON object")

            return result

        except Exception as e:
            error_text = str(e)

            # ---------------------------------------------------------
            # 1. MODEL ERROR → DO NOT RETRY
            # ---------------------------------------------------------
            if "model_not_found" in error_text or "404" in error_text:
                print(f"   ❌ MODEL ERROR: {e}")
                print(f"   ❌ Current model: {MODEL}")
                print("   ❌ Change MODEL to a currently supported Groq model.")
                return None

            # ---------------------------------------------------------
            # 2. RATE LIMIT / TOKEN LIMIT → DO NOT RETRY
            # ---------------------------------------------------------
            if "429" in error_text or "rate_limit_exceeded" in error_text:
                print(f"   ❌ GROQ RATE LIMIT: {e}")
                print("   ⏭️ Skipping this article without retrying.")
                return None

            # ---------------------------------------------------------
            # 3. OTHER ERRORS → RETRY
            # ---------------------------------------------------------
            print(
                f"   [AI Engine] Attempt {attempt}/{MAX_RETRIES}: {e}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)

    return None
#------------------------------------------------------------------------
#updation8------------------------------------------------


# def build_user_prompt(title: str, content: str) -> str:
#     content_trimmed = (content or "")[:4000].strip()
#     if not content_trimmed:
#         content_trimmed = "(No content body available)"
#     return f"Headline: {title}\n\nArticle Content:\n{content_trimmed}"

#updatetion7

def build_user_prompt(title: str, content: str) -> str:

    content_trimmed = (content or "")[:2500].strip()

    if not content_trimmed:
        content_trimmed = "(No content body available)"

    return f"Headline: {title}\n\nArticle Content:\n{content_trimmed}"

def classify_article(client: Groq, article: Dict) -> Dict:
    title = (article.get("title") or "").strip()
    content = (article.get("content") or "").strip()

    if not title and not content:
        return {"category": "GENERAL_NEWS"}

    user_prompt = build_user_prompt(title, content)
    
    # Stage 1 Validation Evaluation
    stage1 = call_llm(client, CIVIC_VALIDATION_SYSTEM, user_prompt)
    if not stage1:
        return {"category": None}

    status = stage1.get("classification", "NOT_CIVIC")
    confidence = float(stage1.get("confidence", 0.0))
    reason = stage1.get("reason", "")

    if status != "CIVIC_ISSUE" or confidence < CIVIC_CONFIDENCE_THRESHOLD:
        return {"category": "GENERAL_NEWS", "confidence": confidence, "reason": reason}

    # Stage 2 Route Verification Mapping
    stage2 = call_llm(client, DEPARTMENT_SYSTEM, user_prompt)
    if not stage2:
        return {
            "category": "CIVIC_ISSUE",
            "confidence": confidence,
            "concerned_department": "MANUAL_REVIEW",
            "issue_type": "Other",
            "locality": "Ludhiana",
            "severity": "Medium"  # Safe MySQL ENUM Fallback
        }

    #dept_confidence = float(stage2.get("dept_confidence", 0.0))
    # department = stage2.get("concerned_department", "MANUAL_REVIEW")
    
    # if dept_confidence < DEPT_CONFIDENCE_THRESHOLD or not department:
    #     department = "MANUAL_REVIEW"
    dept_confidence = float(stage2.get("dept_confidence", 0.0)) 
    department = str( stage2.get("concerned_department", "") ).strip()
    # =========================================================== # ALLOWED TOP-LEVEL DEPARTMENTS # ===========================================================
    ALLOWED_DEPARTMENTS = { "Municipal Corporation Ludhiana",
                            "Ludhiana Traffic Police", 
                            "Punjab Health Department" 
    }
    # Reject invalid department returned by LLM 
    if department not in ALLOWED_DEPARTMENTS: 
        department = "MANUAL_REVIEW"
    # Reject low-confidence routing
    if dept_confidence < DEPT_CONFIDENCE_THRESHOLD: 
        department = "MANUAL_REVIEW"

    # Normalize localized arrays back into character sets for standard text row inserts
    loc_data = stage2.get("locality")
    if isinstance(loc_data, list):
        #loc_data = ", ".join(loc_data)
        loc_data = ", ".join(loc_data[:15])   # more headroom now
        loc_data = str(loc_data)[:490]        # safety cap just under column size

    # -----------------------------------------------------------
    # SEVERITY ENUM SANITIZATION FOR MYSQL
    # -----------------------------------------------------------
    raw_severity = str(stage2.get("severity", "Medium")).strip().capitalize()
    
    # Strict mapping dictionary to prevent MySQL 'Data truncated' (1265) error
    severity_map = {
        "Critical": "High",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low"
    }
    
    clean_severity = severity_map.get(raw_severity, "Medium")

    return {
        "category": "CIVIC_ISSUE",
        "confidence": confidence,
        "concerned_department": department,
        "issue_type": stage2.get("issue_type", "Other"),
        "locality": loc_data if loc_data else "Ludhiana",
        "severity": clean_severity
    }
# ==============================
# PIPELINE EXECUTION ENGINE
# ==============================
def run_classifier(limit: Optional[int] = None):
    init_db()
    articles = get_unclassified_articles(limit)

    if not articles:
        print("✅ No unclassified data vectors found in MySQL.")
        return

    client = Groq(api_key=GROQ_API_KEY)
    total = len(articles)
    
    print(f"\n🚀 Processing {total} articles using Two-Stage Engine Layer ({MODEL})...")

    for idx, art in enumerate(articles, start=1):
        headline_summary = (art.get("title") or "Untitled")[:50]
        print(f"[{idx}/{total}] Checking: '{headline_summary}...'")

        result = classify_article(client, art)
        cat = result.get("category")

        if cat == "CIVIC_ISSUE":
            insert_issue(
                article_id=art["id"],
                title=art["title"],
                link=art["link"],
                source=art["source"],
                issue=result.get("issue_type"),
                department=result.get("concerned_department"),
                severity=result.get("severity", "Medium"),
                location=result.get("locality", "Ludhiana")
            )
            print(f"   📌 DETECTED: {result.get('issue_type')} -> Directed to {result.get('concerned_department')}")
        elif cat == "GENERAL_NEWS":
            insert_issue(
                article_id=art['id'],
                title=art['title'],
                link=art['link'],
                source=art['source'],
                issue='General News',
                department='None',
                severity='Low',  # Capital 'L' to match ENUM('Low', 'Medium', 'High')
                location='Ludhiana'
            )
            print(f"   ⏩ SKIPPED: (General News) | Score: {result.get('confidence', 0.0):.2f}")
        else:
            print("   ❌ PIPELINE DROPPED: Retrying request loop execution next interval run.")

        if idx % 10 == 0:
            time.sleep(BATCH_SLEEP)

if __name__ == "__main__":
    run_classifier()

# if __name__ == "__main__":
#     run_classifier()
#updation3---------------------------------
# if __name__ == "__main__":
#     reclassify_existing_civic_issues()

#updation4----------------------
# if __name__ == "__main__":
#     reclassify_existing_civic_issues(limit=31)
