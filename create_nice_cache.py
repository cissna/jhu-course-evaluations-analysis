from CourseCache import CourseCache


def make_cache_nice(cache_file='cache.json', output_file='nice_cache.json'):
    cache = CourseCache(cache_file)

    sanity_check = []
    
    # modify in place because it's easy:
    for key in list(cache.data.keys()):
        # intersession and summer was too much to deal with and honestly:
        # it's probably valuable to think of them as seperated like I have them right now, anyways.

        if not cache.data[key]['metadata']["relevant_periods"]:
            del cache.data[key]
            continue

        
        # only metadata not easily extractable from data.
        # in fact, this is pretty interesting becaeuse it allows you to extrapolate which periods they did NOT run.
        cache.data[key]["first_period_gathered"] = cache.data[key]['metadata']["first_period_gathered"]
        cache.data[key]["last_period_gathered"] = cache.data[key]['metadata']["last_period_gathered"]
        del cache.data[key]['metadata']

    new_cache = CourseCache(output_file)
    new_cache.data = cache.data
    new_cache.save()


if __name__ == "__main__":
    make_cache_nice()
