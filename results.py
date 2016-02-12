import re
import datetime
from collections import defaultdict


TIMING_COMPANIES = {'leone': {'identifier': 'www.leonetiming.com',
                              'fields': ['place', 'name', 'age', 'time',
                                         'pace', 'age_place', 'age_group',
                                         'sex', 'sex_place', 'residence',
                                         'state'],
                              'divider': '-',
                              },
                    'tnt': {'identifier': 'www.tnttiming.com',
                            'fields': ['place', 'name', 'age', 'sex', 'time',
                                       'pace', 'age_place', 'age_group',
                                       'residence', 'state'],
                            'divider': '=',
                            },
                    }


def pad_lines(in_path):
    """Return all the lines in the file, padded to the width of the max line"""
    out_lines = []
    with open(in_path, 'r') as infile:
        lines = infile.readlines()
        max_len = max([len(line) for line in lines])
        for line in lines:
            len_diff = max_len - len(line)
            line = line[:-1] + ' ' * len_diff + '\n'
            out_lines.append(line)
    return out_lines


def identify_company(lines):
    """Identify the company providing the timing"""
    for line in lines:
        content = line.strip()
        for company in TIMING_COMPANIES:
            if TIMING_COMPANIES[company]['identifier'] == content:
                return company
    return None


def isolate_results(lines):
    """Isolate just the lines containing individual results.

    Assumes that after the last divider line will be all the results until a
    blank line, then no more results. This is true for Leone and TNT. Will have
    to modify this if there are others for whom this does not hold true."""
    out_lines = []
    divider_found = False
    for line in lines:
        if is_divider_line(line):
            divider_found = True
            out_lines = []
        elif divider_found and line.strip() == '':
            break
        else:
            out_lines.append(line)
    return out_lines


def identify_fixed_widths(result_lines):
    columns = zip(*result_lines)
    stops = []
    for i, col in enumerate(columns):
        if ''.join(col).strip() == '':
            stops.append(i)
    return stops


def is_divider_line(line):
    c = line[0]
    if line.strip() == '':
        return False
    elif line.replace(c, '').strip() == '':
        return True
    else:
        return False

# TODO: here is what I want at the end of the day:
# one function where the input is a file and a format hint, and the output is
# a bunch of result objects. Let the caller figure out what to do with it.


# TODO: after I have parsers for all the timing companies I need, figure out
# how to programmatically determine which parser to use. For instance, leone
# has their url on the 5th line, counting the title as the first line
def pivot(path, startline, endline):
    # stops at one column because blank lines are not padded with spaces
    # they have only the one character in them
    with open(path, 'r') as f:
        cols = zip(*f.readlines())
        for c in cols:
            print(c)


def find_fieldwidths(path):
    with open(path, 'r') as f:
        begin_boundaries = []
        end_boundaries = []
        word_begin = None
        word_end = None
        last_divider_line = None
        line_no = 0
        for line in f:
            line_no += 1
            if is_divider_line(line):
                last_divider_line = line_no
            if last_divider_line is not None and line.strip() == '':
                # all space line divides the results from the AG results where
                # applicable
                break
            line_begin_points = []
            line_end_points = []
            for c in range(len(line)):
                if line[c] != ' ' and not word_begin:
                    word_begin = c
                    word_end = None
                elif line[c] != ' ' and word_begin:
                    word_end = c
                elif line[c] == ' ' and word_begin:
                    if word_end is None:
                        word_end = word_begin
                    line_begin_points.append(word_begin)
                    line_end_points.append(word_end)
                    word_begin = None
                    word_end = None
            begin_boundaries.append(line_begin_points)
            end_boundaries.append(line_end_points)
    # now we have big lists of all the word begin and end points for each line
    # figure out which are present in all the lines. First though, get rid of
    # everything before the last divider line.
    begin_boundaries = begin_boundaries[last_divider_line:]
    end_boundaries = end_boundaries[last_divider_line:]
    total_results = len(begin_boundaries)
    print('processing %i results for fixed-width boundaries' % total_results)
    begin_counts = defaultdict(int)
    for line in begin_boundaries:
        for x in line:
            begin_counts[x] += 1
    end_counts = defaultdict(int)
    for line in end_boundaries:
        for x in line:
            end_counts[x] += 1
    begin_items = list(begin_counts.items())
    begin_items.sort(key=lambda x: -x[1])
    end_items = list(end_counts.items())
    end_items.sort(key=lambda x: -x[1])


# TODO: one function gets a list of lists of boundaries for each line

# TODO: one function finds the bounds of the results lines so we can slice

# TODO: one function collects the counts and tells us what fields we have and
# whether they are right or left justified.


# TNT Timing Services: www.tnttiming.com
tnt_result = r'''^                      # start of line
                 \s*(\d+)               # place
                 \s+([\w\s]+?)          # name
                 \s+(\d{1,3})           # age
                 \s+([MF])              # sex
                 \s+([\d:]*)            # time
                 \s+([\d:]*)            # pace
                 \s+(\d+/\d+)           # age group place / total in group
                 \s+([MF]\d+-\d+)       # age group
                 \s+([\w\s]+?)          # residence
                 \s+(\w{2,})            # state abbr
                 \s*$                   # eol
              '''
tnt_location = r'''^                            # start of line
                   \s*(.*?,\s+\w{2,})           # city, state abbr
                   \s+(\d{1,2}/\d{1,2}/\d{4})   # date (%m/%d/%Y)
                   \s*$                         # eol
                '''
tnt_result_regex = re.compile(tnt_result, re.VERBOSE)
tnt_location_regex = re.compile(tnt_location, re.VERBOSE)


def tnt_parser(path):
    # TODO: refactor to combine like code with leone_parser
    # see samples\tnt.txt for what we're parsing
    with open(path, 'r') as race_file:
        # see samples\leone.txt for what we're doing
        race_name = None
        race_location = None
        race_date = None
        dashed_line_count = 0
        results = []
        for line in race_file:
            if line.strip() == '' and not results:
                continue
            elif line.strip() == '':
                break
            elif race_name is None:
                race_name = line.strip()
                print('race_name: %s' % race_name)
            elif race_location is None:
                location_parts = tnt_location_regex.match(line)
                race_location = location_parts.group(1)
                race_date = datetime.datetime.strptime(location_parts.group(2),
                                                       '%m/%d/%Y').date()
                print('race_location: %s' % race_location)
                print('race_date: %s' % race_date)
            elif dashed_line_count < 2:
                if line.startswith('='*20):
                    dashed_line_count += 1
                else:
                    # skip this line
                    pass
            else:
                result_parts = tnt_result_regex.match(line)
                if result_parts is None:
                    print('need to fix the regex')
                    print(line)
                else:
                    # print('result_parts: %s' % (result_parts.groups(),))
                    result = {'place': int(result_parts.group(1)),
                              'name': result_parts.group(2),
                              'age': int(result_parts.group(3)),
                              'sex': result_parts.group(4),
                              'residence': result_parts.group(9),
                              'state': result_parts.group(10),
                              }
                    # print('result: %s' % result)
                    results.append(result)
    print('%i results processed' % len(results))


# LEONE TIMING: leonetiming.com
leone_result = r'''^                    # start of line
                   \s*(\d+)             # place
                   \s+([\w\s]+?)\s{2}   # name
                   \s*(\d{1,3})         # age
                   \s+([\d:]*)          # time
                   \s+([\d:]*)          # pace
                   \s+(\d+/\d+)         # age group place / total in group
                   \s+([MF]\d+-\d+)     # age group
                   \s+([MF])\#          # sex
                   \s+(\d+)             # sex place
                   \s+([\w\s]+?)\s{2}   # residence
                   \s*(\w{2,})          # state abbr
                   \s*$                 # eol
               '''
leone_location = r'''^                          # start of line
                     \s*(.*?,\s+\w{2,})         # city, state
                     \s+(\w+\s\d+,\s\d{4})      # date (%B %d, %Y)
                     \s*$                       # eol
                  '''
leone_result_regex = re.compile(leone_result, re.VERBOSE)
leone_location_regex = re.compile(leone_location, re.VERBOSE)


def leone_parser(path):
    with open(path, 'r') as race_file:
        # see samples\leone.txt for what we're doing
        race_name = None
        race_location = None
        race_date = None
        dashed_line_count = 0
        results = []
        for line in race_file:
            if line.strip() == '' and not results:
                continue
            elif line.strip() == '':
                break
            elif race_name is None:
                race_name = line.strip()
                print('race_name: %s' % race_name)
            elif race_location is None:
                location_parts = leone_location_regex.match(line)
                race_location = location_parts.group(1)
                race_date = datetime.datetime.strptime(location_parts.group(2),
                                                       '%B %d, %Y').date()
                print('race_location: %s' % race_location)
                print('race_date: %s' % race_date)
            elif dashed_line_count < 2:
                if line.startswith('-'*20):
                    dashed_line_count += 1
                else:
                    # skip this line
                    pass
            else:
                result_parts = leone_result_regex.match(line)
                if result_parts is None:
                    print('need to fix the regex')
                else:
                    # print('result_parts: %s' % (result_parts.groups(),))
                    result = {'place': int(result_parts.group(1)),
                              'name': result_parts.group(2),
                              'age': int(result_parts.group(3)),
                              'sex': result_parts.group(8),
                              'residence': result_parts.group(10),
                              'state': result_parts.group(11),
                              }
                    print('result: %s' % result)
                    results.append(result)
    print('%i results processed' % len(results))


if __name__ == '__main__':
    # leone_parser(r'.\samples\leone.txt')
    # tnt_parser(r'.\samples\tnt.txt')
    # find_fieldwidths(r'.\samples\tnt.txt')
    # find_fieldwidths(r'.\samples\leone.txt')
    # pivot(r'.\samples\tnt.txt')
    leone = r'.\samples\leone.txt'
    lines = pad_lines(leone)
    company = identify_company(lines)
    result_lines = isolate_results(lines)
    field_stops = identify_fixed_widths(result_lines)
    print('company: %s' % company)
    print('count result_lines: %s' % len(result_lines))
    print('field_stops: %s' % (field_stops,))

    tnt = r'.\samples\tnt.txt'
