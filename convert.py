# Script to convert CSV to IIF output.

import csv
import os
import sys, traceback, re


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

HEADER_TEMPLATE = "!ACCNT\tNAME\tACCNTTYPE\tDESC\tACCNUM\tEXTRA\r\n"\
                 + "ACCNT\t{account}\tBANK\r\n"\
                 + "ACCNT\tBusiness Misc. Expense\tEXP\r\n"\
                 + "!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
                 + "!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
                 + "!ENDTRNS\r\n"


#output_file.write(template.format(transaction_type, date, account, name, amount, memo,
#                                  transaction_type, date, name, -amount, memo))


FORMAT_DESCRIPTORS = {
  'usbank_checking': {
    'csv_columns' : ['date', 'transaction', 'name', 'memo', 'amount'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{name}\t{amount:.2f}\t{memo}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{memo}\tN\r\n"\
                   + "ENDTRNS\r\n",
    'is_credit_account' : False
  },
  'capitalone_credit_card': {
    'csv_columns' : ['date', 'posted_date', 'last4', 'name', 'memo', 'amount'],
    'transaction': "TRNS\t{transaction_type}\t{date}\t{account}\t{name}\t{amount:.2f}\t{memo}\tN\r\n"\
                   + "SPL\t{transaction_type}\t{date}\tBusiness Misc. Expense\t{name}\t{negative_amount:.2f}\t{memo}\tN\r\n"\
                   + "ENDTRNS\r\n",
    'is_credit_account' : True
  }

}


def error(trans):
  sys.stderr.write("%s\n" % trans)
  traceback.print_exc(None, sys.stderr)

def main(input_file_name):
  print("Converting {} ...".format(input_file_name))
  input_file = open(os.path.join(PROJECT_ROOT, input_file_name), 'r')
  #output_file = open(os.path.join(PROJECT_ROOT, input_file_name + '.iif'), 'w')

  output_filename = '/mnt/Pool1/backup-src/' + input_file_name + '.iif'
  #output_filename = os.path.join(PROJECT_ROOT, input_file_name + '.iif')

  print("Output filename = {}".format(output_filename))

  output_file = open(output_filename, 'w')

  # This is the name of the QuickBooks checking account
  account = 'US Bank Checking'
  descriptor = FORMAT_DESCRIPTORS['usbank_checking']
  csv_columns = descriptor['csv_columns']
  template = descriptor['transaction']
  is_credit_account = descriptor['is_credit_account']

  # This is the IIF template

  #head = "!TRNS	TRNSID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	TOPRINT	NAMEISTAXABLE	DUEDATE	TERMS	PAYMETH	SHIPVIA	SHIPDATE	REP	FOB	PONUM	INVMEMO	ADDR1	ADDR2	ADDR3	ADDR4	ADDR5	SADDR1	SADDR2	SADDR3	SADDR4	SADDR5	TOSEND	ISAJE	OTHER1	ACCTTYPE	ACCTSPECIAL\r\n"\
  #       + "!SPL	SPLID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	QNTY	PRICE	INVITEM	PAYMETH	TAXABLE	EXTRA	VATCODE	VATRATE	VATAMOUNT	VALADJ	SERVICEDATE	TAXCODE	TAXRATE	TAXAMOUNT	TAXITEM	OTHER2	OTHER3	REIMBEXP	ACCTTYPE	ACCTSPECIAL	ITEMTYPE\r\n"\
  #+ "!ENDTRNS\r\n"
  # head = "!ACCNT\tNAME\tACCNTTYPE\tDESC\tACCNUM\tEXTRA\r\n"\
  # + "ACCNT\t{}\tBANK\r\n".format(account)
  #
  # head += "ACCNT\tBusiness Misc. Expense\tEXP\r\n"\
  # + "!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
  # + "!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
  # + "!ENDTRNS\r\n"

  head = HEADER_TEMPLATE.format(account=account)

  output_file.write(head)

  #template = "TRNS		CHECK	%s	%s	 %s		%s		N	N	%s																			N			CCARD\r\n"\
  #           + "SPL		CHECK	%s	Ask My Accountant			%s				0	%s							0.00					0.00					EXP\r\n"\
  #+ "ENDTRNS\r\n"

  # template = "TRNS\t{}\t{}\t{}\t{}\t{}\t{}\tN\r\n"\
  # + "SPL\t{}\t{}\tBusiness Misc. Expense\t{}\t{}\t{}\tN\r\n"\
  # + "ENDTRNS\r\n"

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

        transaction_type = 'DEPOSIT'

        try:
          for i, field in enumerate(csv_columns):
            x = row[i]

            if field == 'amount':
              amount = x = float(x)

              if is_credit_account:
                amount = -amount

              data['negative_amount'] = -amount

              if amount < 0:
                transaction_type = 'CHECK'
            else:
              x = x.strip()

            data[field] = x
        except:
          error(str(row))
          continue


        # template = "TRNS\tCHECK\t3/1/2018\tUS Bank Checking\tSome Junky Expense\t-10000\tThis is a check\tN\r\n"\
        # + "SPL\tCHECK\t3/1/2018\tBusiness Misc. Expense\tSome Junky Expense\t10000\tThis is a check\tN\r\n"\
        # + "ENDTRNS\r\n"

        data['transaction_type'] = transaction_type

        print("data = " + str(data))


        output_file.write(template.format(**data))

  print('Done.')

if __name__ == '__main__':

  if len(sys.argv) != 2:
      print("usage:   python convert.py input.csv")

  main(sys.argv[1])
