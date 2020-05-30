def read_config_file(fname):
    settings = {}

    with open(fname, 'r') as f:
        for line in f:
            slist = line.split('=', 1)
            if len(slist) >= 2:
                prefix, suffix = slist
                settings[prefix.strip()] = suffix.strip()

    return settings
