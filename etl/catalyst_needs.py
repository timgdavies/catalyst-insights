source_details = {
	"title":"Catalyst COVID19 Charity Needs",
	"contactName":"Joseph Dudley & Tim Davies",
	"email":"joseph@wearecast.org.uk",
	"description":"A collection of charity needs recorded by the Catalyst team and partners during early stages of COVID-19 Pandemic.",
	"license":"tbc",
	"url":"https://airtable.com/tblXFm7FAb5qHkeoM",
	"consentPolicyDescription":"tbc"
}

import getpass
from airtable import Airtable
import os
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
import dateutil.parser

import sys
sys.path = ['', '..'] + sys.path[1:]

from insight_models import *

def update_obj(_self, props):
	for k, v in props.items():
		setattr(_self, k, v)

# Database schema specific mapping
def map_request_state(state):
	mapping = {
		"Addressed":"addressed",
		"Unaddressed":"active",
		"":None
	}
	return mapping.get(state, None)

# Airtable specific lookup helper
def create_lookup(base_id, table_name, view_name):
	lookup = {}

	airtable = Airtable(base_id,table_name)	
	for page in airtable.get_iter(view=view_name):
		for record in page:
			lookup[record['id']] = record['fields']

	return lookup

# TODO: Add taxonomy support
def needs_list_lookup(session, need):
	
	need = session.query(NeedsList).filter(NeedsList.title==need).first()
	if(need):
		return need
	else:
		need = NeedsList(title = need)
		session.add(need)
		return need


if __name__ == '__main__':
	# First we get an API Key
	if not os.environ.get('AIRTABLE_API_KEY'):
	  os.environ['AIRTABLE_API_KEY'] = getpass.getpass("Please input your AirTable API Key.\n\nYour key can be found at https://airtable.com/account \n\n")

	## Setup database connection
	connection_string = os.getenv('CATALYST_INSIGHT_DB','sqlite:///../catalyst-insights.db')
	engine = create_engine(connection_string)
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	## Add or update the source
	source = session.query(Source).filter_by(title=source_details['title']).first()
	if source:
		update_obj(source, source_details)
		session.add(source)	
	else:
		print("Creating source")
		source = Source(**source_details)
		session.add(source)


	## Drop existing data from 

	## Connect to AirTable
	base_id = 'appKjedGx8WllrhjV'

	# Get our lookup tables
	topics = create_lookup(base_id, "Topics", "Grid view")
	user_need = create_lookup(base_id, "User Needs", "Grid view")

	airtable = Airtable(base_id, "Charity Messages")	
	for page in airtable.get_iter(view="MASTER"):
		for record in page:
			need = {}
			need['technologyNeeds'] = record['fields'].get('Message','')
			need['requesterName'] = record['fields'].get('From','')
			try:
				need['requestDate']= dateutil.parser.parse(record['fields'].get('Date',None))
			except TypeError:
				pass
			need['requestState'] = map_request_state(record['fields'].get('Status',''))
			need['source'] = source

			if(record['fields'].get('From',None)):
				organisation = session.query(Organisation).filter(or_(Organisation.name==record['fields'].get('From'),
																		 Organisation.alternateName==record['fields'].get('From'))).first()
				if organisation:
					pass #We don't have anything to add.
				else:
					organisation = Organisation(name = record['fields'].get('From'),
												alternateName = record['fields'].get('From'))
					session.add(organisation)

				need['organisation'] = organisation

			need['relatedNeeds'] = []
			for need_id in record['fields'].get('Topics',[]):
				needs_list_entry = needs_list_lookup(session, topics[need_id]['Name'])
				need['relatedNeeds'].append(needs_list_entry)

			db_need = SupportNeed(**need)

			session.add(db_need)
	
	## Commit updates
	session.commit()