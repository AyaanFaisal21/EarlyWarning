// The five queries the demo is built on. Q3 is the one to end on.
//
// Every one of these is a set operation, an absence test, or a multi-hop traversal.
// None can be expressed as similarity search — that is the argument for the graph, and it
// is worth saying out loud while one of them is on screen.

// ===========================================================================  Q0
// Frequency ranking vs potential ranking. Run both, show they disagree.
// This is the Heinrich critique made concrete: the most COMMON hazard is not the most
// DANGEROUS one, which is exactly why counting near-misses failed as a strategy.

MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
RETURN p.title AS pattern, count(e) AS occurrences
ORDER BY occurrences DESC LIMIT 5;

MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
WHERE e.sif_potential IN ['high', 'fatal']
RETURN p.title AS pattern, count(e) AS could_have_killed_someone
ORDER BY could_have_killed_someone DESC LIMIT 5;


// ===========================================================================  Q1
// The reporting gap: patterns the cameras saw repeatedly that produced no report at all.
//
// NOT (e)-[:GENERATED]->(:Report) is a negation over a relationship. A vector index has no
// way to express "and nothing points at this" — the nearest-neighbour answer to an absence
// question is silently wrong.

MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH p, count(e) AS occurrences, count(r) AS reports
WHERE reports = 0 AND occurrences >= 3
RETURN p.title AS pattern, occurrences
ORDER BY occurrences DESC;


// ===========================================================================  Q2
// What the safety committee should actually look at this month.
//
// unseen_risk = accumulated SIF weight x the fraction that stayed invisible. It ranks
// "dangerous AND nobody knows" above both "dangerous but already tracked" and "frequent but
// harmless". This is the ranking that replaces counting.

MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH p,
     count(e) AS occurrences,
     count(r) AS reports,
     sum(CASE e.sif_potential
           WHEN 'fatal'    THEN 8.0
           WHEN 'high'     THEN 4.0
           WHEN 'moderate' THEN 2.0
           WHEN 'low'      THEN 1.0
           ELSE 0.0 END) AS sif_weight
WITH p, occurrences, reports, sif_weight,
     sif_weight * (1.0 - toFloat(reports) / occurrences) AS unseen_risk
RETURN p.title AS pattern,
       occurrences,
       reports,
       round(unseen_risk, 1) AS unseen_risk
ORDER BY unseen_risk DESC
LIMIT 10;


// ===========================================================================  Q3
// Normalization of deviance, computed.  <-- end the demo here
//
// Vaughan's mechanism is that a practice drifts until it stops feeling wrong, and nobody
// notices because no one compares today against two years ago. That leaves a signature:
//
//     occurrences rising  +  safety margin shrinking  +  report rate falling
//
// An organisation is not becoming safer here. It is becoming desensitised. This query is
// the reason the project is called institutional memory rather than video analytics.
//
// :param split => datetime('2026-06-29T00:00:00Z')

MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH p, e, (r IS NOT NULL) AS reported
WITH p,
     sum(CASE WHEN e.occurred_at >= $split THEN 1 ELSE 0 END) AS n_recent,
     sum(CASE WHEN e.occurred_at <  $split THEN 1 ELSE 0 END) AS n_prior,
     // avg() skips nulls, so 'not_applicable' proximities drop out on their own
     avg(CASE WHEN e.occurred_at >= $split THEN e.proximity_ord END) AS prox_recent,
     avg(CASE WHEN e.occurred_at <  $split THEN e.proximity_ord END) AS prox_prior,
     sum(CASE WHEN e.occurred_at >= $split AND reported THEN 1 ELSE 0 END) AS rep_recent,
     sum(CASE WHEN e.occurred_at <  $split AND reported THEN 1 ELSE 0 END) AS rep_prior
WHERE n_prior >= 3 AND n_recent >= 3
WITH p, n_prior, n_recent, prox_prior, prox_recent,
     toFloat(rep_prior)  / n_prior  AS rate_prior,
     toFloat(rep_recent) / n_recent AS rate_recent
WHERE prox_recent < prox_prior AND rate_recent < rate_prior
RETURN p.title                          AS pattern,
       n_prior                          AS before_count,
       n_recent                         AS now_count,
       round(prox_prior, 2)             AS proximity_before,
       round(prox_recent, 2)            AS proximity_now,
       round(rate_prior * 100)          AS reported_pct_before,
       round(rate_recent * 100)         AS reported_pct_now,
       round((prox_prior - prox_recent) * n_recent, 2) AS drift_score
ORDER BY drift_score DESC;


// ===========================================================================  Q4
// The action. Which single absent control buys the most risk reduction?
//
// Two hops from Control back through Event to Pattern. This is what makes the output a
// work order instead of a dashboard — end on something someone can go and do.

MATCH (c:Control)<-[:MISSING_CONTROL]-(e:Event)-[:INSTANCE_OF]->(p:Pattern)
WHERE e.sif_potential IN ['high', 'fatal']
RETURN c.name                        AS absent_control,
       count(DISTINCT e)             AS high_potential_events,
       count(DISTINCT p)             AS distinct_patterns,
       collect(DISTINCT p.title)[..3] AS example_patterns
ORDER BY high_potential_events DESC;


// ===========================================================================  Q5
// The one job the graph cannot do — and the reason Marengo is in the stack.
//
// Given an event somebody DID report, find the ones nobody reported that look like it.
// Fingerprints group by causal structure and will miss a near-identical event that got a
// slightly different control assessment; embeddings catch exactly that.
//
// :param event_id => 'ev-0001'
//
// db.index.vector.queryNodes is deprecated as of Neo4j 2026.04 but still works on every
// version including older Docker images. On 2026.01+ the SEARCH clause is preferred.

MATCH (seed:Event {id: $event_id})
CALL db.index.vector.queryNodes('event_embedding', 25, seed.embedding)
YIELD node AS similar, score
WHERE similar.id <> seed.id
  AND NOT (similar)-[:GENERATED]->(:Report)
RETURN similar.id            AS event,
       similar.description   AS description,
       similar.sif_potential AS sif_potential,
       round(score, 3)       AS similarity
ORDER BY similarity DESC
LIMIT 10;
