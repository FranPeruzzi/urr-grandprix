import openpyxl
import datetime


class Member:
    def __init__(self, drn, lname, fname, city, state, sex, dob):
        self.drn = drn
        self.lname = lname
        self.fname = fname
        self.city = city
        self.state = state
        self.sex = sex
        if not isinstance(dob, (datetime.date, datetime.datetime)):
            err_msg = 'Member.__init__ age requires datetime.date/datetime'
            raise ValueError(err_msg)
        if isinstance(dob, datetime.datetime):
            dob = dob.date()
        self.dob = dob

    def __str__(self):
        s = '<Member %s: %s, %s. DOB: %s, Sex: %s>'
        return s % (self.drn, self.lname, self.fname, self.dob, self.sex)

    def age(self, as_of=None):
        if as_of is None:
            as_of = datetime.date.today()
        if not isinstance(as_of, (datetime.date, datetime.datetime)):
            err_msg = 'Member.age requires datetime.date or datetime.datetime'
            raise ValueError(err_msg)
        age = as_of.year - self.dob.year
        if (as_of.month, as_of.day) < (self.dob.month, self.dob.day):
            age -= 1
        return age

    def in_age_group(self, group_min, group_max, as_of=None):
        age = self.age(as_of=as_of)
        return group_min <= age <= group_max


# Just testing to make sure this works.
# TODO: Need to put this into one or more functions.
src_path = r'roster.xlsx'
sheet_name = 'Sheet1'
# TODO: create a command line argument for src_path. Required.
# TODO: allow for filetypes besides xlsx
# TODO: create a command line arguemnt for sheet_name. If not present, use
# index 0

wb = openpyxl.load_workbook(src_path, data_only=True, guess_types=True)
sh = wb.get_sheet_by_name(sheet_name)
header = None
members = []
for row in sh.iter_rows(row_offset=1):
    # TODO: set up a configurable row parser
    # skip the totals row
    if row[0].value in ('Total', None):
        continue
    # can't particpate in the grand prix if we don't know your age or sex
    if str(row[14].value).strip().lower() not in ('m', 'f'):
        continue
    if row[15].value in ('', None):
        continue
    field_indices = [0, 6, 7, 10, 11, 14, 15]
    fields = [row[i].value for i in field_indices]
    m = Member(*fields)
    print(m, 'Age %i' % m.age())
    members.append(m)

print('Members processed: %i' % len(members))
