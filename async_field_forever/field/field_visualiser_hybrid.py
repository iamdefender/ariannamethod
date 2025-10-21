def get_terminal_config():
    term_w = ...  # Assuming this is defined earlier
    base_width = min(term_w - 2, 78)  # Max 78, minus 2 for margins

    return {
        "banner_width": base_width,  # Everything same width!
        "grid_w": base_width - 4,  # Grid slightly narrower for padding
        # Other configurations...
    }