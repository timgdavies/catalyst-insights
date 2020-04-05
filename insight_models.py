import os
import sys
import enum
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, Date, Enum, Table, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class SharingConsent(enum.Enum): ## TODO: Work out the levels that should be used here
  """What permissions do we have to share certain information? Based on the [ODI Data Spectrum](https://theodi.org/about-the-odi/the-data-spectrum/)"""
  private = 'private'
  shared = 'shared'
  open = 'open'

class Source(Base):
  """Each support need, resource or statistic should have a recorded source. 
  
  Source information allows is used to determine the legitimate use of information 
  and to provide appropriate attribution."""
  __tablename__ = 'source'
  pk =Column(Integer, primary_key=True)
  title = Column(String(250))
  contactName = Column(String(250))
  email = Column(String(250))
  description = Column(String(250))
  license = Column(String(250))
  url = Column(String(250))
  consentPolicyDescription = Column(Text)

organisation_locations = Table('organisation_locations', 
                           Base.metadata,
                           Column('organisation_pk', Integer, ForeignKey('organisation.pk')),
                           Column('location_type',String(250)),
                           Column('location_pk',Integer, ForeignKey('location.pk'))
                          )

organisation_classifications = Table('organisation_classification', 
                           Base.metadata,
                           Column('organisation_pk', Integer, ForeignKey('organisation.pk')),
                           Column('classification_pk',Integer, ForeignKey('classification.pk'))
                          )


class Organisation(Base):
  """The organisation table follows the `360 Giving Schema for Organisations <http://standard.threesixtygiving.org/en/latest/reference/#giving-json-schemas>`_

  Only public organisation-level contact information should be stored in this table."""
  __tablename__ = 'organisation'
  """Test"""
  pk = Column(Integer, primary_key=True)
  id = Column(String(250))
  """360 Giving organisation identifiers are strings."""
  name = Column(String(250))
  """Organisation name."""
  alternateName = Column(String(250)) 
  """Used for other names the charity is known as."""
  department = Column(String(250)) 
  """Department can b used to record any form of sub-division (e.g. local branch name for a federated organisation)."""
  contactName = Column(String(250))
  """Only publicly available contact names should be used."""
  charityNumber = Column(String(250)) 
  """Validated against Charity Commission data where possible."""
  companyNumber = Column(String(250)) 
  """Validated against Companies House where possible."""
  streetAddress = Column(String(250))
  """Building number and street name."""
  addressLocality = Column(String(250))
  """City or Town."""
  addressRegion = Column(String(250))
  """County."""
  addressCountry = Column(String(250))
  """Country."""
  postalCode = Column(String(250))
  """Postal code (used for geocoding)."""
  telephone = Column(String(250))
  """Only publicly available organisational contact details should be provided."""
  email = Column(String(250))
  """Only publicly available organisational contact details should be provided."""
  description = Column(Text)
  """A short description of this organisation's focus."""
  url = Column(String(250))
  """Link to this organisations primary web presence."""
  locations = relationship("Location",secondary=organisation_locations)
  """Zero or more locations where this organisation works."""
  classifications = relationship("Classification",secondary=organisation_classifications)
  """Any classifications applied to this organisation."""
  dateModified = Column(DateTime)
  """Last modified time of this organisation record."""

class SupportRequestState(enum.Enum):
  example = 'example' # This is an example of a request, but we do not need to act on it
  new = 'new' # This is a new request, requiring triage
  active = 'active' # This is an active request, needing response
  addressed = 'addressed' # This request has been addressed in some form

supportNeedMapping = Table('needs_mapping', 
                           Base.metadata,
                           Column('support_need_pk', Integer, ForeignKey('support_need.pk')),
                           Column('provenance',String(250)),
                           Column('needs_list_pk',Integer, ForeignKey('needs_list.pk'))
                          )
                          

class SupportNeed(Base):
  """Support needs are made up of three key components:

  - A context: explaining the work or project the need relates to
  - A description of the need
  - Existing resources: that the requester has to draw upon in meeting the need

  """
  __tablename__ = 'support_need'
  pk = Column(Integer, primary_key=True)
  organisation_pk =Column(Integer, ForeignKey('organisation.pk'))
  organisation = relationship(Organisation)
  """If this request can be linked to a specific organisation, record that here."""
  requesterName = Column(String(250))
  requesterEmail = Column(String(250))
  requesterPhone = Column(String(250))
  requesterRole = Column(String(250))
  needContext = Column(Text)
  """A brief description of the work of the organisation or project that will aid an understanding of needs."""
  technologyNeeds = Column(Text)
  """Describe any technology related needs: e.g. access to hardware; use of particular tools and platforms."""
  serviceDeliveryNeeds = Column(Text)
  """Describe any needs related to designing and delivering services."""
  operationsNeeds = Column(Text)
  """Describe any needs relating to operations: e.g. skills for remote working as a team."""
  fundingNeeds = Column(Text)
  """Describe any needs related to funding, including fundraising."""
  generalNeeds = Column(Text)
  """Describe any needs not captured (or not possible to divide) into the other need categories."""
  existingResources = Column(Text)
  """If the requester has existing resources to draw upon, these can be recorded here."""
  digitalMaturity = Column(String(250))
  """A codelist value to describe the level of digital maturity of the requesting organisation/project."""
  needHorizon = Column(String(250)) # shortTerm, midTerm, longTerm 
  notes = Column(Text)
  """For internal notes added during import or handling a need request."""
  requestDate = Column(DateTime)
  requestState = Column(Enum(SupportRequestState), nullable=True)
  """To indicate if this need has been met, or if it requires action."""
  sharingConsent = Column(Enum(SharingConsent), nullable=True)
  followUpConsentsHeldBy = Column(String(250))
  """Who has permission to go back to this requester to follow up?"""
  relatedNeeds = relationship("NeedsList",secondary=supportNeedMapping)
  source_pk = Column(Integer, ForeignKey('source.pk'))
  source = relationship(Source)
  dateModified = Column(DateTime)

class NeedsList(Base):
  __tablename__ = 'needs_list'
  pk =Column(Integer, primary_key=True)
  title = Column(String(250))
  description = Column(Text)
  notes = Column(Text)
  parent_pk =Column(Integer, ForeignKey('needs_list.pk'))
  dateModified = Column(DateTime)
  
class Resource(Base):
  __tablename__ = 'resource'
  pk =Column(Integer, primary_key=True)
  title = Column(String(250))
  description = Column(Text)
  notes = Column(Text)
  url = Column(Text)
  providedByOrganisation_pk =Column(Integer, ForeignKey('organisation.pk'))
  providedByOrganisation = relationship(Organisation)
  meetsNeed_pk =Column(Integer, ForeignKey('needs_list.pk'))
  meetsNeed = relationship(NeedsList)
  dateModified = Column(DateTime)

class Location(Base):
  __tablename__ = 'location'
  pk = Column(Integer, primary_key=True)
  id = Column(String(250)) # 360 Giving location identifiers may be strings
  name = Column(String(250))
  countryCode = Column(String(250))
  latitude = Column(Numeric)
  longitude = Column(Numeric)
  geoCode = Column(String(250))
  geoCodeType = Column(String(250)) # See https://github.com/ThreeSixtyGiving/standard/blob/master/codelists/geoCodeType.csv 
  dateModified = Column(DateTime)

class Classification(Base):
  __tablename__ = 'classification'
  pk = Column(Integer, primary_key=True)
  vocabulary = Column(String(250))
  code = Column(String(250))
  title = Column(String(250))
  url = Column(String(250))
  description = Column(Text)


if __name__ == '__main__':
	connection_string = os.getenv('CATALYST_INSIGHT_DB','sqlite:///catalyst-insights.db')
	engine = create_engine(connection_string)
	Base.metadata.create_all(engine) 

	# Draw diagram
	from sqlalchemy_schemadisplay import create_schema_graph
	from sqlalchemy import MetaData

	graph = create_schema_graph(metadata=MetaData(connection_string),
	                            show_datatypes=True,
	                            show_indexes=True,
	                            rankdir='LR',
	                            concentrate=True)

	graph.write_png("database.png")

# from IPython.display import Image
# Image('database.png')

