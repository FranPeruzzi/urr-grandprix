import re
import datetime


# fields with None are discarded
TIMING_COMPANIES = {'leone': {'identifier': 'www.leonetiming.com',
                              'fields': ['place', 'name', 'age', None, None,
                                         None, None, 'sex', None, 'residence',
                                         'state'],
                              'date_fmt': '%B %d, %Y',
                              },
                    'tnt': {'identifier': 'www.tnttiming.com',
                            'fields': ['place', 'name', 'age', 'sex', None,
                                       None, None, None, 'residence', 'state'],
                            'date_fmt': '%m/%d/%Y',
                            },
                    }


def process_file(path):
    lines = pad_lines(path)
    results = parse_results(lines)
    return results


def pad_lines(in_path):
    """Return all the lines in the file, padded to the width of the max line"""
    out_lines = []
    with open(in_path, 'r') as infile:
        lines = infile.readlines()
        max_len = max([len(line) for line in lines])
        for line in lines:
            if not out_lines and line.strip() == '':
                continue
            len_diff = max_len - len(line)
            line = line[:-1] + ' ' * len_diff + '\n'
            out_lines.append(line)
    return out_lines


def parse_results(lines):
    company = identify_company(lines)
    if company not in TIMING_COMPANIES:
        raise Exception('Unrecognized format for results file')
    company_info = TIMING_COMPANIES[company]
    race_info = parse_header(lines, company_info['date_fmt'])
    race_info['results'] = []
    result_lines = isolate_results(lines)
    stops = identify_fixed_widths(result_lines)
    # print('stops: %s' % (stops,))
    for line in result_lines:
        result = {}
        for i, fieldname in enumerate(TIMING_COMPANIES[company]['fields']):
            if fieldname is None:
                continue
            low_stop = stops[i]
            if i < (len(stops)-1):
                high_stop = stops[i+1]
            else:
                high_stop = -1
            result[fieldname] = line[low_stop:high_stop].strip()
        # print(result)
        race_info['results'].append(result)
    return race_info


def identify_company(lines):
    """Identify the company providing the timing"""
    for line in lines:
        content = line.strip()
        for company in TIMING_COMPANIES:
            if TIMING_COMPANIES[company]['identifier'] == content:
                return company
    return None


def parse_header(lines, date_fmt):
    # I thought too much about this, and I'm just going to throw back the first
    # two nonblank lines.
    name = lines[0].strip()
    # location, date = [s.strip() for s in lines[1].strip().split('  ')]
    location, race_date = re.split(r'\s{2,}', lines[1].strip(), 2)
    race_date = datetime.datetime.strptime(race_date, date_fmt).date()
    print('race_date: %s' % race_date)
    return {'name': name, 'location': location, 'date': race_date}


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
        if ''.join(col).strip() != '':
            if stops and stops[-1] == i-1:
                stops[-1] = i
            else:
                stops.append(i)
    stops = [i+1 for i in stops]
    stops.insert(0, 0)
    return stops


def is_divider_line(line):
    c = line[0]
    if line.strip() == '':
        return False
    elif line.replace(c, '').strip() == '':
        return True
    else:
        return False


if __name__ == '__main__':
    leone = r'.\samples\leone.txt'
    leone_results = process_file(leone)

    tnt = r'.\samples\tnt.txt'
    tnt_results = process_file(tnt)
