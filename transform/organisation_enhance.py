## This is a test only - working against UK Charity Commmission Charities

import os
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker
import requests
import sys

sys.path = ['', '..'] + sys.path[1:]
from insight_models import *

def classification_lookup(session, title, vocabulary):
	
	classification = session.query(Classification).filter(Classification.title==title).first()
	if(classification):
		return classification
	else:
		classification = Classification(title=title, vocabulary=vocabulary)
		session.add(classification)
		return classification



if __name__ == '__main__':
	## Setup database connection
	connection_string = os.getenv('CATALYST_INSIGHT_DB','sqlite:///../catalyst-insights.db')
	engine = create_engine(connection_string)
	DBSession = sessionmaker(bind=engine)
	session = DBSession()

	headers={"Authorization":"Apikey {}".format(os.getenv('CHARITYBASE_API_KEY',''))}

	for organisation in session.query(Organisation).filter_by(id=None):
		query = """{
		  CHC {
		    getCharities(filters: {
		      search: "%s"
		    }) {
		      count
		      list(limit: 3) {
		        id
		        names {
		          value
		          primary
		        }
		        activities
		      }
		    }
		  }
		}""" % organisation.name

		print("=======SEARCHING FOR =========")
		print(organisation.name)
		print("==============================")		

		r = requests.get("https://charitybase.uk/api/graphql", params={"query":query}, headers=headers)
		n = 1
		try:
			print("Nearest matches are shown below...\n\n")
			for charity in r.json()['data']['CHC']['getCharities']['list']:
				print("{}. {} \n {} \n\n".format(n, charity['names'][0]['value'], charity['activities']))
				n = n + 1
		except Exception:
			print(Exception)
			print("No options found")

		if n > 1:
			selection = input(">>> Select 1 - {} for one of the options above, enter a charity number manually, or press enter to skip.\n> ".format(n-1))
		else: 
			selection = input(">>> No matching charities found. Please manually enter a charity number, or press enter to skip.\n> ")

		if(selection):
			if(selection.isnumeric()):
				if len(selection) < 2:
					charity_id = r.json()['data']['CHC']['getCharities']['list'][int(selection)-1]['id']
				else:
					charity_id = selection
				print(charity_id)

				# Now we query for the charity
				query = """{
					  CHC {
					    getCharities(filters: {
					      id:"%s"
					    }) {
					      count
					      list(limit: 3) {
					        id
					        names {
					          value
					          primary
					        }
					        activities
					        contact {
					          email
					          person
					          phone
					          postcode
					        }
					        website
					        activities
					        causes {
					          id
					          name
					        }
					        beneficiaries{
					          id
					          name
					        }
					        operations {
					          id
					          name
					        }
					        numPeople {
					          employees
					          trustees
					          volunteers
					        }
					      }
					    }
					  }
					}""" % charity_id
				r = requests.get("https://charitybase.uk/api/graphql", params={"query":query}, headers=headers)
				if(len(r.json()['data']['CHC']['getCharities']['list']) > 0):
					org_data = r.json()['data']['CHC']['getCharities']['list'][0]
					organisation.name = org_data['names'][0]['value']
					organisation.charityNumber = str(org_data['id'])
					organisation.id = "GB-CHC-"+str(org_data['id'])
					organisation.postalCode = org_data['contact']['postcode']
					organisation.email = org_data['contact']['email']
					organisation.url = org_data['website']
					organisation.description = org_data['activities']
					for cause in org_data['causes']:
						organisation.classifications.append(classification_lookup(session, cause['name'], 'CHC_causes'))
					for beneficiary in org_data['beneficiaries']:
						organisation.classifications.append(classification_lookup(session, beneficiary['name'], 'CHC_beneficiaries'))
					for operation in org_data['operations']:
						organisation.classifications.append(classification_lookup(session, operation['name'], 'CHC_operations'))
					session.add(organisation)
			else:
				print("Only numeric values are permitted")
		else:
			print("Skipping {}".format(organisation.name))

	session.commit()

		