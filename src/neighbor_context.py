"""Pack retrieved chunks with immediate source neighbors."""

from starter.baseline import pack_context


def pack_neighbor_context(results, corpus, budget=2500):
    groups = {}
    by_id = {}

    for chunk in corpus:
        by_id[chunk["id"]] = chunk
        metadata = chunk["metadata"]
        key = (
            chunk["source_id"],
            chunk["page"],
            metadata["unit_id"],
        )
        groups.setdefault(key, []).append(chunk)

    neighbors = {}

    for rows in groups.values():
        rows.sort(
            key=lambda chunk: (
                chunk["metadata"]["start_char"],
                chunk["id"],
            )
        )

        for position, chunk in enumerate(rows):
            adjacent = []

            # Prefer continuation, then preceding context.
            for index in (position + 1, position - 1):
                if 0 <= index < len(rows):
                    other = rows[index]
                    left, right = sorted(
                        (chunk, other),
                        key=lambda item: item["metadata"]["start_char"],
                    )

                    # Do not bridge an unretrieved source gap.
                    if (
                        right["metadata"]["start_char"]
                        <= left["metadata"]["end_char"]
                    ):
                        adjacent.append(other["id"])

            neighbors[chunk["id"]] = adjacent

    expanded = []
    seen = set()
    seed_ids = {chunk["id"] for chunk in results}

    for seed in results:
        for chunk_id in [seed["id"], *neighbors[seed["id"]]]:
            if chunk_id in seen:
                continue
            seen.add(chunk_id)

            chunk = by_id[chunk_id]
            reference = by_id[seed["id"]]

            if chunk["metadata"]["section"] != reference["metadata"]["section"]:
                raise ValueError("Neighbor crosses the section boundary.")

            expanded.append({
                **chunk,
                "context_origin": (
                    "retrieved" if chunk_id in seed_ids else "neighbor"
                ),
            })

    context, ids = pack_context(expanded, budget=budget)
    selected = set(ids)
    included = [
        chunk for chunk in expanded if chunk["id"] in selected
    ]

    return context, ids, included