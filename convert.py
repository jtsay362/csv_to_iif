# Script to convert CSV to IIF output.

import csv
import os
import sys, traceback, re


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))


def error(trans):
  sys.stderr.write("%s\n" % trans)
  traceback.print_exc(None, sys.stderr)

def main(input_file_name):
  print "Converting %s ..." % input_file_name
  input_file = open(os.path.join(PROJECT_ROOT, input_file_name), 'r')
  #output_file = open(os.path.join(PROJECT_ROOT, input_file_name + '.iif'), 'w')
  output_file = open('/mnt/Pool1/backup-src/usbank_checking_2017.iif', 'w')

  # This is the name of the QuickBooks checking account
  account = 'US Bank Checking'

  # This is the IIF template

  #head = "!TRNS	TRNSID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	TOPRINT	NAMEISTAXABLE	DUEDATE	TERMS	PAYMETH	SHIPVIA	SHIPDATE	REP	FOB	PONUM	INVMEMO	ADDR1	ADDR2	ADDR3	ADDR4	ADDR5	SADDR1	SADDR2	SADDR3	SADDR4	SADDR5	TOSEND	ISAJE	OTHER1	ACCTTYPE	ACCTSPECIAL\r\n"\
  #       + "!SPL	SPLID	TRNSTYPE	DATE	ACCNT	NAME	CLASS	AMOUNT	DOCNUM	MEMO	CLEAR	QNTY	PRICE	INVITEM	PAYMETH	TAXABLE	EXTRA	VATCODE	VATRATE	VATAMOUNT	VALADJ	SERVICEDATE	TAXCODE	TAXRATE	TAXAMOUNT	TAXITEM	OTHER2	OTHER3	REIMBEXP	ACCTTYPE	ACCTSPECIAL	ITEMTYPE\r\n"\
  #+ "!ENDTRNS\r\n"
  head = "!ACCNT\tNAME\tACCNTTYPE\tDESC\tACCNUM\tEXTRA\r\n"\
  + "ACCNT\t%s\tBANK\r\n" % (account)

  head += "ACCNT\tBusiness Misc. Expense\tEXP\r\n"\
  + "!TRNS\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
  + "!SPL\tTRNSTYPE\tDATE\tACCNT\tNAME\tAMOUNT\tMEMO\tCLEAR\r\n"\
  + "!ENDTRNS\r\n"

  output_file.write(head)

  #template = "TRNS		CHECK	%s	%s	 %s		%s		N	N	%s																			N			CCARD\r\n"\
  #           + "SPL		CHECK	%s	Ask My Accountant			%s				0	%s							0.00					0.00					EXP\r\n"\
  #+ "ENDTRNS\r\n"

  template = "TRNS\t%s\t%s\t%s\t%s\t%s\t%s\tN\r\n"\
  + "SPL\t%s\t%s\tBusiness Misc. Expense\t%s\t%s\t%s\tN\r\n"\
  + "ENDTRNS\r\n"

  found_header = False

  with input_file:
    csv_reader = csv.reader(input_file)

    with output_file:
      for row in csv_reader:
        if not found_header:
          found_header = True
          continue

        try:
          (date, debit_or_credit, name, memo, amount) = row
        #            date = date.replace('/', '-')
        except:
          error(str(row))
          continue

        try:
          amount = float(amount)
        except:
          error(str(row))
          continue

        transaction_type = 'DEPOSIT'

        if amount < 0:
          transaction_type = 'CHECK'

        # template = "TRNS\tCHECK\t3/1/2018\tUS Bank Checking\tSome Junky Expense\t-10000\tThis is a check\tN\r\n"\
        # + "SPL\tCHECK\t3/1/2018\tBusiness Misc. Expense\tSome Junky Expense\t10000\tThis is a check\tN\r\n"\
        # + "ENDTRNS\r\n"

        output_file.write(template % (transaction_type, date, account, name, amount, memo,
                                      transaction_type, date, name, -amount, memo))

  print "Done."

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print "usage:   python convert.py input.csv"

    main(sys.argv[1])