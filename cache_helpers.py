from CourseCache import CourseCache

def combine_entries(entry1: str, entry2: str, cache_file: str=None) -> dict:
    """The purpose of this function is to deal with scenarios like CS 400 level and 600 level courses where the entries really should be combined

    Args:
        entry1 (str): CourseCache key, should be a course code or can be a course code with |IN or |SU at the end
        entry2 (str): the secondary entry. The above course code will be used, but all the values at this entry will be in the final entry
        cache_file (str, optional): if not specified, just cache.json, but you can use another file if you want

    Returns:
        dict: a (cache entry)-style object
    """
    cache = CourseCache() if cache_file is None else CourseCache(cache_file)

    e1 = cache.data[entry1]  # the default one
    e2 = cache.data[entry2]

    rel1 = set(e1['metadata']['relevant_periods'])
    rel2 = set(e2['metadata']['relevant_periods'])
    for period in (rel1 & rel2):  # if no overlap, skip this, all is well
        for specific_course, specific_course_entry in e2['data'][period].items():
            assert(specific_course not in e1['data'][period])
            e1['data'][period][specific_course] = specific_course_entry

    e1['metadata']['relevant_periods'] = rel1 | rel2
    assert(e1['metadata']['first_period_gathered'] == e2['metadata']['first_period_gathered'])
    assert(e1['metadata']['last_period_gathered'] == e2['metadata']['last_period_gathered'])
    assert(not e1['metadata']['failed_periods'] and not e2['metadata']['failed_periods'])

    return e1


if __name__ == "__main__":
    print(combine_entries('EN.601.482', 'EN.601.682'))
