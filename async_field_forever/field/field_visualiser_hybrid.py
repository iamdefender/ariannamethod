def get_terminal_config():
    """Auto-detect terminal size and return adaptive config."""
    try:
        term_w, term_h = shutil.get_terminal_size((80, 24))
    except:
        term_w, term_h = 80, 24
    
    is_mobile = term_w < 70
    base_width = min(term_w - 2, 78)  # Max 78, minus 2 for margins
    
    return {
        "term_w": term_w,
        "term_h": term_h,
        "is_mobile": is_mobile,
        "banner_width": base_width,
        "grid_w": base_width - 4,
        "grid_h": 12 if is_mobile else 18,
        "pulse_bar_w": base_width - 10,
        "cell_list_limit": 2 if is_mobile else 4,
        "grid_padding_left": 2,
    }