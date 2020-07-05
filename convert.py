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
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{name}\t{amount:.2f}\t{memo}\tY\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{memo}\tY\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'BANK',
    'is_credit_account' : False
  },
  'usbank_credit_card': {
    'csv_columns' : ['date', 'transaction', 'name', 'memo', 'amount'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{name}\t{amount:.2f}\t{memo}\tY\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{memo}\tY\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'CCARD',
    'is_credit_account' : True
  },
  'capitalone_credit_card': {
    'csv_columns' : ['transaction_date', 'posted_date', 'card_num_last4', 'name', 'category', 'debit', 'credit'],
    'transaction': "TRNS\t{transaction_type}\t{transaction_date}\t{account}\t{name}\t{amount:.2f}\t{category}\tY\r\n"\
                   + "SPL\t{transaction_type}\t{transaction_date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{category}\tY\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'CCARD',
    'is_credit_account' : True
  },
  'citibank_credit_card' : {
    'csv_columns' : ['status', 'date', 'description', 'debit', 'credit', 'member_name'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{description}\t{amount:.2f}\t{member_name}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{description}\t{negative_amount:.2f}\t{member_name}\tY\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'CCARD',
    'is_credit_account' : True
  },
  'citibank_credit_card_annual_summary' : {
    'csv_columns' : ['date', 'description', 'debit', 'credit', 'category'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{description}\t{amount:.2f}\t{category}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{description}\t{negative_amount:.2f}\t{category}\tY\r\n"\
                   + "ENDTRNS\r\n",
    'account_type' : 'CCARD',
    'is_credit_account' : True
  },

}

Y_M_D_RE = re.compile('(\d{4})[\-/]([01]?\d)[\-/]([0-3]?\d)')
M_D_Y_RE = re.compile('([01]?\d)[\-/]([0-3]?\d)[\-/](\d{4})')


def compute_transaction_type(is_credit_account, amount):
  if is_credit_account:
    if amount <= 0:
      return 'CREDIT CARD'
    else:
      return 'CC CREDIT'
  else:
    if amount < 0:
      return 'CHECK'
    else:
      return 'DEPOSIT'

import sys, traceback, re

def error(trans):
  sys.stderr.write("%s\n" % trans)
  traceback.print_exc(None, sys.stderr)

def main(args):
  print(f"Converting {args.input_filename} ...")
  input_file = open(args.input_filename, 'r')
  #output_file = open(os.path.join(PROJECT_ROOT, input_file_name + '.iif'), 'w')

  base_filename = os.path.basename(args.input_filename)

  output_filename = base_filename[:base_filename.rfind('.csv')] + '.iif'

  output_filename = os.path.join(args.output_dir, output_filename)  

  print(f"Output filename = {output_filename}")

  output_file = open(output_filename, 'w')

  # This is the name of the QuickBooks checking account
  account = args.account_name or 'US Bank Checking'

  print(f"Account name = {account}")

  # This is the name of the QuickBooks checking account
  #account = 'US Bank Checking'

  format = args.format or 'usbank_checking'

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
        print(row)

        if not found_header:
          found_header = True
          continue

        data = {
          'account': account
        }

        amount = None

        try:
          for i, field in enumerate(csv_columns):
            inner_amount = None

            x = row[i]

            if field == 'amount':
              inner_amount = float(x)
            elif field.endswith('date'):
                d = None

                m = Y_M_D_RE.match(x.strip())

                if m:
                  print("Date matches YYYY-MM-DD")
                  d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                else:
                  m = M_D_Y_RE.match(x.strip())

                  if m:
                    print("Date matches MM-DD-YYYY")
                    d = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

                if d:
                  x = d.strftime('%m/%d/%Y')
                else:
                  print("Non-matching date " + x)

            elif len(x) > 0:
              if field == 'debit':
                inner_amount = -float(x)
              elif field == 'credit':
                inner_amount = float(x)

            if inner_amount is None:
              x = x.strip()
              data[field] = x
            else:
              amount = inner_amount

        except:
          error(str(row))
          continue

        if amount is None:
          amount = 0

        data['amount'] = amount
        data['negative_amount'] = -amount

        data['transaction_type'] = compute_transaction_type(is_credit_account, amount)

        print("data = " + str(data))


        output_file.write(template.format(**data))

  print('Done.')

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Convert a CSV file to IIF format.')
  parser.add_argument('input_filename', help='Filename of CSV file to convert')      
  parser.add_argument('-o', '--output-dir', help='Output directory', default=".")
  parser.add_argument('-a', '--account-name', help='Name of the account')
  parser.add_argument('-f', '--format', help='Format of CSV file', default='usbank_checking')
  
  main_args = parser.parse_args()

  main(main_args)
