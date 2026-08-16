"""Optional image-matching adapter.

The core system remains fully functional without a vision model. A deployment
can replace this adapter with CLIP/embedding-backed scoring when it has model
weights, compute, and an approved image-retention policy.
"""


def image_similarity(source, candidate, enabled=False):
    """Return ``None`` when visual matching is unavailable, never a made-up score."""
    if not enabled or not source.image_filename or not candidate.image_filename:
        return None
    # Intentionally a stable extension point, not a pseudo-AI comparison.
    return None
