import yaml
import io

import os, django

# from django.contrib.gis.geoip2.resources import Country

os.environ['DJANGO_SETTINGS_MODULE'] = 'portfolio_ecom.settings'
django.setup()
from core.models import Category, Country


# data = {
# 	'a list': [
# 		1,
# 		42,
# 		3.141,
# 		1337,
# 		'help',
# 		u'€'
# 	],
# 	'a string': 'bla',
# 	'another dict': {
# 		'foo': 'bar',
# 		'key': 'value',
# 		'the answer': 42
# 	}
# }

def write_data(data):
	"""
	:type data: dict
	"""
	with io.open('data.yaml', 'w', encoding='utf8') as outfile:
		try:
			yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)
		except yaml.YAMLError as exc:
			print(exc)


# return dict
def get_file_data() -> dict:
	with open('data.yaml', 'r') as stream:
		try:
			return yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			print(exc)


class CategoryData:
	name = 'core_category'
	
	@classmethod
	def tofile(cls, data: dict = None):
		arr = []
		for r in Category.objects.all():
			arr.append({
				'id': r.id,
				'name': r.name,
				'parent': r.parent,
				'is_selectable': r.is_selectable
			})
		write_data({cls.name: arr})
	
	@classmethod
	def todb(cls, data: dict = None):
		for i in get_file_data()[cls.name]:
			Category(**i).save()


class CountryData:
	name = 'core_country'
	
	@classmethod
	def tofile(cls, data: dict = None, override=False):
		if data is None:
			arr = []
			for r in Category.objects.all():
				arr.append({
					'id': r.id,
					'name': r.name,
				})
			write_data({cls.name: arr})
		else:
			yaml_data = get_file_data()
			if not override:  # if append
				if not cls.name in yaml_data:
					yaml_data[cls.name] = []
					for index, item in enumerate(data):
						item['id'] = index
						yaml_data[cls.name].append(item)
				else:
					max2 = 0
					if len(yaml_data[cls.name]) > 0:
						arr = []
						for item in yaml_data[cls.name]:
							arr.append(float(item['id']))
						max2 = max(arr) + 1
					
					for index, item in enumerate(data):
						item['id'] = index + max2
						yaml_data[cls.name].append(item)
			else:
				yaml_data[cls.name] = []
				for index, item in enumerate(data):
					item['id'] = index
					yaml_data[cls.name].append(item)
	
	@classmethod
	def todb(cls, data: list = None, override=False):
		if data is None:
			for i in get_file_data()[cls.name]:
				Country(**i).save()
		else:
			if not override:  # if append
				for i in data:
					if 'id' in i:
						raise Exception('can\'t override with id, remove the id')
					Country(**i).save()
			else:
				for i in data:
					if 'id' not in i:
						raise Exception('if you want to override you need id')
					el = Country.objects.get(id=i['id'])
					el.name = i['name']

					
# CategoryData.tofile()
# CategoryData.todb()

# test if exist replace else create yaml
# data = get_file_data()
# data['sambal'][2] = {
# 	'wow': '555555555555555',
# 	'wow111111111111': 'dam',
# 	'wow1111111112': 'dam',
# 	'wodddddddw3': 'dam',
# }
#
# write_data(data)

CountryData.todb([
	{'name': 'Sri Lanka', },
	{'name': 'India', },
	{'name': 'USA', },
	{'name': 'Germany', },
])
