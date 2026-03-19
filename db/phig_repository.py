import json
from uuid import uuid4

from db.session import async_session


async def _fetchone_dict(session, query: str, params: dict):
    result = await session.execute(query, params)
    row = result.mappings().first()
    return dict(row) if row else None


def _parse_json(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


async def persist_document_graph(
    patient_id: str,
    document_id: str,
    source_type: str,
    medications: list[dict],
    labs: list[dict],
    interaction_alerts: list[dict] | None = None,
):
    """
    Persist extracted graph data into phig_nodes/phig_edges.
    Returns counts and mutates medication/lab items with generated phig_node_id.
    """
    interaction_alerts = interaction_alerts or []

    try:
        async with async_session() as session:
            med_node_ids = {}
            lab_node_ids = {}
            created_nodes = 0
            created_edges = 0

            for med in medications:
                name = (med.get("name") or "").strip()
                if not name:
                    continue

                metadata = {
                    "document_id": document_id,
                    "source_type": med.get("source_type", source_type),
                    "ocr_confidence": med.get("ocr_confidence"),
                    "ner_match": bool(med.get("ner_match") or med.get("rxnorm")),
                    "verified": bool(med.get("verified", False)),
                    "dosage": med.get("dosage"),
                    "frequency": med.get("frequency"),
                    "prescribed_by_doctor": med.get("prescribed_by_doctor"),
                    "prescribed_on": med.get("prescribed_on"),
                    "duration_days": med.get("duration_days"),
                    "is_ongoing": med.get("is_ongoing"),
                }

                existing = await _fetchone_dict(
                    session,
                    """
                    SELECT id
                    FROM phig_nodes
                    WHERE patient_id = :pid
                      AND node_type = 'medication'
                      AND lower(display_name) = lower(:name)
                      AND is_active = TRUE
                    LIMIT 1
                    """,
                    {"pid": patient_id, "name": name},
                )

                if existing:
                    node_id = existing["id"]
                    await session.execute(
                        """
                        UPDATE phig_nodes
                        SET dosage = :dosage,
                            frequency = :frequency,
                            rxnorm_code = :rxnorm,
                            confidence_score = :confidence,
                            confidence_source = :source,
                            metadata = CAST(:metadata AS jsonb),
                            updated_at = NOW()
                        WHERE id = :id
                        """,
                        {
                            "id": node_id,
                            "dosage": med.get("dosage"),
                            "frequency": med.get("frequency"),
                            "rxnorm": med.get("rxnorm"),
                            "confidence": float(med.get("confidence") or 0.0),
                            "source": med.get("source_type", source_type),
                            "metadata": json.dumps(metadata),
                        },
                    )
                else:
                    node_id = str(uuid4())
                    await session.execute(
                        """
                        INSERT INTO phig_nodes (
                            id, patient_id, node_type, display_name,
                            rxnorm_code, dosage, frequency,
                            confidence_score, confidence_source,
                            metadata, is_active
                        ) VALUES (
                            :id, :pid, 'medication', :name,
                            :rxnorm, :dosage, :frequency,
                            :confidence, :source,
                            CAST(:metadata AS jsonb), TRUE
                        )
                        """,
                        {
                            "id": node_id,
                            "pid": patient_id,
                            "name": name,
                            "rxnorm": med.get("rxnorm"),
                            "dosage": med.get("dosage"),
                            "frequency": med.get("frequency"),
                            "confidence": float(med.get("confidence") or 0.0),
                            "source": med.get("source_type", source_type),
                            "metadata": json.dumps(metadata),
                        },
                    )
                    created_nodes += 1

                med["phig_node_id"] = node_id
                med_node_ids[name.lower()] = node_id

            for lab in labs:
                name = (lab.get("name") or "").strip()
                if not name:
                    continue

                metadata = {
                    "document_id": document_id,
                    "source_type": source_type,
                    "verified": False,
                    "unit": lab.get("unit"),
                    "ref_low": lab.get("ref_low"),
                    "ref_high": lab.get("ref_high"),
                }

                existing = await _fetchone_dict(
                    session,
                    """
                    SELECT id
                    FROM phig_nodes
                    WHERE patient_id = :pid
                      AND node_type = 'lab_result'
                      AND lower(display_name) = lower(:name)
                      AND is_active = TRUE
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    {"pid": patient_id, "name": name},
                )

                if existing:
                    node_id = existing["id"]
                    await session.execute(
                        """
                        UPDATE phig_nodes
                        SET value = :value,
                            unit = :unit,
                            reference_range_low = :ref_low,
                            reference_range_high = :ref_high,
                            is_abnormal = :abnormal,
                            confidence_score = :confidence,
                            confidence_source = :source,
                            metadata = CAST(:metadata AS jsonb),
                            updated_at = NOW()
                        WHERE id = :id
                        """,
                        {
                            "id": node_id,
                            "value": float(lab.get("value") or 0.0),
                            "unit": lab.get("unit"),
                            "ref_low": lab.get("ref_low"),
                            "ref_high": lab.get("ref_high"),
                            "abnormal": (
                                (lab.get("ref_high") is not None and float(lab.get("value") or 0.0) > float(lab.get("ref_high")))
                                or (lab.get("ref_low") is not None and float(lab.get("value") or 0.0) < float(lab.get("ref_low")))
                            ),
                            "confidence": float(lab.get("confidence") or 0.86),
                            "source": source_type,
                            "metadata": json.dumps(metadata),
                        },
                    )
                else:
                    node_id = str(uuid4())
                    await session.execute(
                        """
                        INSERT INTO phig_nodes (
                            id, patient_id, node_type, display_name,
                            value, unit, reference_range_low, reference_range_high,
                            is_abnormal, confidence_score, confidence_source,
                            metadata, is_active
                        ) VALUES (
                            :id, :pid, 'lab_result', :name,
                            :value, :unit, :ref_low, :ref_high,
                            :abnormal, :confidence, :source,
                            CAST(:metadata AS jsonb), TRUE
                        )
                        """,
                        {
                            "id": node_id,
                            "pid": patient_id,
                            "name": name,
                            "value": float(lab.get("value") or 0.0),
                            "unit": lab.get("unit"),
                            "ref_low": lab.get("ref_low"),
                            "ref_high": lab.get("ref_high"),
                            "abnormal": (
                                (lab.get("ref_high") is not None and float(lab.get("value") or 0.0) > float(lab.get("ref_high")))
                                or (lab.get("ref_low") is not None and float(lab.get("value") or 0.0) < float(lab.get("ref_low")))
                            ),
                            "confidence": float(lab.get("confidence") or 0.86),
                            "source": source_type,
                            "metadata": json.dumps(metadata),
                        },
                    )
                    created_nodes += 1

                lab["phig_node_id"] = node_id
                lab_node_ids[name.lower()] = node_id

            # Link medications to current labs for traversal (HAS_LAB)
            for med_id in med_node_ids.values():
                for lab_id in lab_node_ids.values():
                    existing_edge = await _fetchone_dict(
                        session,
                        """
                        SELECT id
                        FROM phig_edges
                        WHERE patient_id = :pid
                          AND source_node_id = :src
                          AND target_node_id = :dst
                          AND edge_type = 'HAS_LAB'
                          AND is_active = TRUE
                        LIMIT 1
                        """,
                        {"pid": patient_id, "src": med_id, "dst": lab_id},
                    )
                    if not existing_edge:
                        await session.execute(
                            """
                            INSERT INTO phig_edges (
                                id, patient_id, source_node_id, target_node_id,
                                edge_type, is_active, metadata
                            ) VALUES (
                                :id, :pid, :src, :dst,
                                'HAS_LAB', TRUE, CAST(:metadata AS jsonb)
                            )
                            """,
                            {
                                "id": str(uuid4()),
                                "pid": patient_id,
                                "src": med_id,
                                "dst": lab_id,
                                "metadata": json.dumps({"document_id": document_id}),
                            },
                        )
                        created_edges += 1

            for alert in interaction_alerts:
                pair = str(alert.get("drug_pair") or "")
                if "+" not in pair:
                    continue
                left, right = [p.strip().lower() for p in pair.split("+", 1)]
                left_id = med_node_ids.get(left)
                right_id = med_node_ids.get(right)
                if not left_id or not right_id:
                    continue
                existing_edge = await _fetchone_dict(
                    session,
                    """
                    SELECT id
                    FROM phig_edges
                    WHERE patient_id = :pid
                      AND source_node_id = :src
                      AND target_node_id = :dst
                      AND edge_type = 'INTERACTS_WITH'
                      AND is_active = TRUE
                    LIMIT 1
                    """,
                    {"pid": patient_id, "src": left_id, "dst": right_id},
                )
                if not existing_edge:
                    await session.execute(
                        """
                        INSERT INTO phig_edges (
                            id, patient_id, source_node_id, target_node_id,
                            edge_type, severity, description, clinical_action,
                            is_active, metadata
                        ) VALUES (
                            :id, :pid, :src, :dst,
                            'INTERACTS_WITH', :severity, :description, :action,
                            TRUE, CAST(:metadata AS jsonb)
                        )
                        """,
                        {
                            "id": str(uuid4()),
                            "pid": patient_id,
                            "src": left_id,
                            "dst": right_id,
                            "severity": alert.get("severity"),
                            "description": alert.get("description"),
                            "action": alert.get("clinical_action"),
                            "metadata": json.dumps({"document_id": document_id}),
                        },
                    )
                    created_edges += 1

            await session.commit()
            return {"created_nodes": created_nodes, "created_edges": created_edges, "error": None}
    except Exception as exc:
        # Hard fallback: keep application functional even when DB graph tables are unavailable.
        return {"created_nodes": 0, "created_edges": 0, "error": str(exc)}


async def update_document_medication_confidence(document_id: str, medications: list[dict]):
    try:
        async with async_session() as session:
            for med in medications:
                node_id = med.get("phig_node_id")
                if not node_id:
                    continue
                existing = await _fetchone_dict(
                    session,
                    "SELECT id, metadata FROM phig_nodes WHERE id = :id LIMIT 1",
                    {"id": node_id},
                )
                if not existing:
                    continue
                metadata = _parse_json(existing.get("metadata"))
                metadata.update(
                    {
                        "document_id": document_id,
                        "verified": bool(med.get("verified", False)),
                        "source_type": med.get("source_type"),
                        "ocr_confidence": med.get("ocr_confidence"),
                        "ner_match": bool(med.get("ner_match", False)),
                    }
                )
                await session.execute(
                    """
                    UPDATE phig_nodes
                    SET confidence_score = :confidence,
                        confidence_source = :source,
                        dosage = :dosage,
                        frequency = :frequency,
                        metadata = CAST(:metadata AS jsonb),
                        updated_at = NOW()
                    WHERE id = :id
                    """,
                    {
                        "id": node_id,
                        "confidence": float(med.get("confidence") or 0.0),
                        "source": med.get("source_type", "prescription_photo"),
                        "dosage": med.get("dosage"),
                        "frequency": med.get("frequency"),
                        "metadata": json.dumps(metadata),
                    },
                )
            await session.commit()
    except Exception:
        return


async def load_patient_graph_from_db(patient_id: str) -> dict:
    try:
        async with async_session() as session:
            node_rows = (await session.execute(
                """
                SELECT id, node_type, display_name, rxnorm_code, loinc_code, icd10_code,
                       dosage, frequency, value, unit,
                       reference_range_low, reference_range_high,
                       confidence_score, confidence_source,
                       metadata
                FROM phig_nodes
                WHERE patient_id = :pid AND is_active = TRUE
                """,
                {"pid": patient_id},
            )).mappings().all()

            if not node_rows:
                return {
                    "from_db": False,
                    "medications": [],
                    "labs": [],
                    "conditions": [],
                    "interactions": [],
                    "care_gaps": [],
                }

            by_id = {}
            medications = []
            labs = []
            conditions = []

            for row in node_rows:
                entry = dict(row)
                meta = _parse_json(entry.get("metadata"))
                by_id[entry["id"]] = entry
                node_type = entry.get("node_type")

                if node_type == "medication":
                    medications.append(
                        {
                            "name": entry.get("display_name"),
                            "dosage": entry.get("dosage") or meta.get("dosage") or "",
                            "frequency": entry.get("frequency") or meta.get("frequency") or "",
                            "rxnorm": entry.get("rxnorm_code"),
                            "confidence": float(entry.get("confidence_score") or 0.0),
                            "confidence_label": "VERIFIED" if float(entry.get("confidence_score") or 0.0) >= 0.8 else ("HIGH" if float(entry.get("confidence_score") or 0.0) >= 0.65 else "MODERATE"),
                            "prescribed_by_doctor": meta.get("prescribed_by_doctor"),
                            "prescribed_on": meta.get("prescribed_on"),
                            "duration_days": meta.get("duration_days"),
                            "is_ongoing": meta.get("is_ongoing"),
                            "source_type": entry.get("confidence_source") or meta.get("source_type"),
                            "ocr_confidence": meta.get("ocr_confidence"),
                            "ner_match": meta.get("ner_match"),
                            "verified": meta.get("verified", False),
                            "phig_node_id": entry.get("id"),
                            "interactions": [],
                        }
                    )
                elif node_type == "lab_result":
                    labs.append(
                        {
                            "name": entry.get("display_name"),
                            "value": entry.get("value"),
                            "unit": entry.get("unit"),
                            "ref_low": entry.get("reference_range_low"),
                            "ref_high": entry.get("reference_range_high"),
                            "confidence": float(entry.get("confidence_score") or 0.0),
                            "loinc": entry.get("loinc_code"),
                            "phig_node_id": entry.get("id"),
                        }
                    )
                elif node_type == "condition":
                    conditions.append(
                        {
                            "name": entry.get("display_name"),
                            "code": entry.get("icd10_code"),
                            "confidence": float(entry.get("confidence_score") or 0.0),
                            "phig_node_id": entry.get("id"),
                        }
                    )

            edge_rows = (await session.execute(
                """
                SELECT source_node_id, target_node_id, edge_type, severity, description, clinical_action, metadata
                FROM phig_edges
                WHERE patient_id = :pid AND is_active = TRUE
                """,
                {"pid": patient_id},
            )).mappings().all()

            interactions = []
            for edge in edge_rows:
                edge_type = str(edge.get("edge_type") or "").upper()
                if edge_type != "INTERACTS_WITH":
                    continue
                src = by_id.get(edge.get("source_node_id"))
                dst = by_id.get(edge.get("target_node_id"))
                interactions.append(
                    {
                        "drug_pair": f"{(src or {}).get('display_name', 'Drug A')} + {(dst or {}).get('display_name', 'Drug B')}",
                        "severity": edge.get("severity") or "MODERATE",
                        "description": edge.get("description") or "Potential interaction",
                        "clinical_action": edge.get("clinical_action") or "Review with physician",
                        "acknowledged": False,
                    }
                )

            return {
                "from_db": True,
                "medications": medications,
                "labs": labs,
                "conditions": conditions,
                "interactions": interactions,
                "care_gaps": [],
            }
    except Exception:
        return {
            "from_db": False,
            "medications": [],
            "labs": [],
            "conditions": [],
            "interactions": [],
            "care_gaps": [],
        }
