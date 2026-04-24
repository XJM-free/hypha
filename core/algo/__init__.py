"""Core algorithms. Each module exposes ``prepare(ctx)`` and ``apply(ctx, llm_response)``.

The split lets adapters invoke any LLM CLI between the two calls without Hypha
itself depending on a specific provider. A convenience ``run(ctx, llm_cmd)``
wires them together for users who don't need that flexibility.
"""
