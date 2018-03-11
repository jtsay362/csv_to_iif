# Script to convert CSV to IIF output.

import argparse
import csv
import os
import re
from datetime import date
import sys, traceback

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

HEADER_TEMPLATE = "!ACCNT\tNAME\tACCNTTYPE\tDESC\tACCNUM\tEXTRA\r\n"\
                 + "ACCNT\t{account}\t{account_type}\r\n"\
                 + "ACCNT\tBusiness Misc. Expense\tEXP\r\n"\
                 + "!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
                 + "!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
                 + "!ENDTRNS\r\n"

FORMAT_DESCRIPTORS = {
  'usbank_checking': {
    'csv_columns' : ['date', 'transaction', 'name', 'memo', 'amount'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{name}\t{amount:.2f}\t{memo}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{memo}\tN\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'BANK',
    'is_credit_account' : False
  },
  'capitalone_credit_card': {
    'csv_columns' : ['transaction_date', 'posted_date', 'card_num_last4', 'name', 'category', 'debit', 'credit'],
    'transaction': "TRNS\t{transaction_type}\t{transaction_date}\t{account}\t{name}\t{amount:.2f}\t{category}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{transaction_date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{category}\tN\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'CCARD',
    'is_credit_account' : True
  }
}

Y_M_D_RE = re.compile('(\d{4})[\-/](\d\d)[\-/](\d\d)')


def compute_transaction_type(is_credit_account, amount):
  if is_credit_account:
    if amount < 0:
      return 'CREDIT CARD'
    else:
      return 'CC CREDIT'
  else:
    if amount < 0:
      return 'CHECK'
    else:
      return 'DEPOSIT'


def error(trans):
  sys.stderr.write("%s\n" % trans)
  traceback.print_exc(None, sys.stderr)

def main(input_file_name=None, output_file_name=None, format=None, account=None):
  print("Converting {} ...".format(input_file_name))
  input_file = open(os.path.join(PROJECT_ROOT, input_file_name), 'r')
  #output_file = open(os.path.join(PROJECT_ROOT, input_file_name + '.iif'), 'w')

  output_file_name = '/mnt/Pool1/backup-src/' + input_file_name + '.iif'
  #output_filename = os.path.join(PROJECT_ROOT, input_file_name + '.iif')

  if not output_file_name:
    output_filename = os.path.join(PROJECT_ROOT, input_file_name + '.iif')

  print("Output filename = {}".format(output_file_name))

  output_file = open(output_file_name, 'w')

  # This is the name of the QuickBooks checking account
  #account = 'US Bank Checking'

  if not format:
    format = 'usbank_checking'

  descriptor = FORMAT_DESCRIPTORS[format]
  csv_columns = descriptor['csv_columns']
  template = descriptor['transaction']
  account_type = descriptor['account_type']
  is_credit_account = descriptor['is_credit_account']

  head = HEADER_TEMPLATE.format(account=account, account_type=account_type)

  output_file.write(head)

  found_header = False

  with input_file:
    csv_reader = csv.reader(input_file)

    with output_file:
      for row in csv_reader:
        if not found_header:
          found_header = True
          continue

        print(row)

        data = {
          'account': account
        }

        amount = None

        try:
          for i, field in enumerate(csv_columns):
            x = row[i]

            if field == 'amount':
              amount = float(x)
              if is_credit_account:
                amount = -amount
            elif field.endswith('date'):
                m = Y_M_D_RE.match(x.strip())

                if m:
                  print("Date matches YYYY-MM-DD")
                  d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                  x = d.strftime('%-m/%-d/%Y')
                else:
                  print("Non-matching date " + x)


            elif len(x) > 0:
              if field == 'debit':
                amount = -float(x)
              elif field == 'credit':
                amount = float(x)

            if amount == None:
              x = x.strip()
              data[field] = x
            else:
              data['amount'] = amount
              data['negative_amount'] = -amount

        except:
          error(str(row))
          continue

        data['transaction_type'] = compute_transaction_type(is_credit_account, amount)

        print("data = " + str(data))


        output_file.write(template.format(**data))

  print('Done.')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Convert a CSV file to IIF format.')
  parser.add_argument('input_file_name', metavar='input_file', help='Filename of CSV file to convert')
  parser.add_argument('output_file_name', metavar='output_file', help='Output filename of IIF file', nargs='?')
  parser.add_argument('--account', help='Name of the account to import into', required=True)
  parser.add_argument('--format', help='Format of CSV file', default='usbank_checking')

  args = vars(parser.parse_args())

  main(**args)
