// Graph schema. Run once against an empty database:
//   cat schema.cypher | docker exec -i earlywarning-neo4j cypher-shell -u neo4j -p hackathon2026

// ---------------------------------------------------------------- uniqueness constraints
CREATE CONSTRAINT site_id       IF NOT EXISTS FOR (s:Site)       REQUIRE s.id   IS UNIQUE;
CREATE CONSTRAINT camera_id     IF NOT EXISTS FOR (c:Camera)     REQUIRE c.id   IS UNIQUE;
CREATE CONSTRAINT recording_id  IF NOT EXISTS FOR (r:Recording)  REQUIRE r.id   IS UNIQUE;
CREATE CONSTRAINT event_id      IF NOT EXISTS FOR (e:Event)      REQUIRE e.id   IS UNIQUE;
CREATE CONSTRAINT report_id     IF NOT EXISTS FOR (r:Report)     REQUIRE r.id   IS UNIQUE;
CREATE CONSTRAINT pattern_fp    IF NOT EXISTS FOR (p:Pattern)    REQUIRE p.fingerprint IS UNIQUE;

// Taxonomy nodes are keyed by name, which is what makes MERGE-based entity resolution
// exact rather than fuzzy. This only works because extraction is enum-constrained.
CREATE CONSTRAINT hazard_name   IF NOT EXISTS FOR (h:HazardType) REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT actor_name    IF NOT EXISTS FOR (a:Actor)      REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT control_name  IF NOT EXISTS FOR (c:Control)    REQUIRE c.name IS UNIQUE;

// ------------------------------------------------------------------------------ indexes
CREATE INDEX event_time         IF NOT EXISTS FOR (e:Event)  ON (e.occurred_at);
CREATE INDEX event_sif          IF NOT EXISTS FOR (e:Event)  ON (e.sif_potential);
CREATE INDEX report_time        IF NOT EXISTS FOR (r:Report) ON (r.filed_at);

// Marengo 3.0 is 512-dimensional (it was 1024 in 2.7 — a mismatch here fails silently,
// which is the worst way for it to fail).
CREATE VECTOR INDEX event_embedding IF NOT EXISTS
FOR (e:Event) ON (e.embedding)
OPTIONS { indexConfig: {
  `vector.dimensions`: 512,
  `vector.similarity_function`: 'cosine'
}};

// ------------------------------------------------------------------------- shape summary
//
//   (:Site)-[:HAS_CAMERA]->(:Camera)-[:RECORDED]->(:Recording)-[:CONTAINS]->(:Event)
//
//   (:Event)-[:OF_TYPE]->(:HazardType)
//   (:Event)-[:INVOLVED]->(:Actor)
//   (:Event)-[:MISSING_CONTROL]->(:Control)   <- absence as a first-class edge
//   (:Event)-[:GENERATED]->(:Report)          <- usually absent; that IS the product
//   (:Event)-[:INSTANCE_OF]->(:Pattern)       <- the grouping edge
//
// Two edges do the real work:
//
//   MISSING_CONTROL  makes "which control was absent across the most high-potential events"
//                    a two-hop traversal. In a document store it's a text field you grep.
//
//   GENERATED        is defined by its absence. The reporting gap is
//                    NOT (e)-[:GENERATED]->(:Report) — a set difference, which is precisely
//                    what similarity search cannot express.
