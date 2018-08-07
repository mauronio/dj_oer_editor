#
# Requiere cx_Oracle 
#
# OER Contents

import cx_Oracle
import time
import os

assetsSQL = """ 
	SELECT A.id, A.name AssetName, nvl(A.version, '0'), A.description, nvl(AT.name, 'tipo desconocido') AssetTypeName, AT.id AssetTypeID,  CA.name FunctionName,
               nvl(substr(A.name, 2, instr(A.name, '}', 1, 1)-2), '(Sin  Dominio)') DomainName, 
               nvl(substr(A.name, 
               	instr(A.name, '}', 1, 1) + 1, 
               	instr(A.name, '/', -1, 1) - (instr(A.name, '}', 1, 1)+1)), '(Sin Contexto)') ContextName,
               substr(A.name, instr(A.name, '/', -1, 1) + 1) SimpleName

	 FROM SOAOER.ASSETS A, SOAOER.ASSETTYPES AT, SOAOER.ASSETCATEGORIZATIONS AC, SOAOER.CATEGORIZATIONS CA  
	 where A.AssetTypeID = AT.id 
	  and A.id = AC.assetid  
	  and AC.catid = CA.id 
	  and CA.superid = 50352 
	  and AT.Id = 50204 -- Service Type
	  order by 7, 9, 10
	"""

relacionadosSQL = """
	select SA.id relatedID, SA.name relatedName, RT.displaysecondary relatedrole, RT.name relationship, RT.displayprimary primaryrole, RT.displaysecondary secondaryrole, 
		PA.id primaryID, SA.id secondaryID from soaoer.assetrelationships AR, soaoer.assets PA, soaoer.assets SA, soaoer.relationshiptypes RT 
	where AR.primaryID = PA.id and AR.secondaryid = SA.id and AR.typeid = RT.id and PA.Id = :assetID 
	union  
	select PA.id relatedID, PA.name relatedName, RT.displayprimary relatedrole, RT.name relationship, RT.displayprimary primaryrole, RT.displaysecondary secondaryrole, 
		PA.id primaryID, SA.id secondaryID from soaoer.assetrelationships AR, soaoer.assets PA, soaoer.assets SA, soaoer.relationshiptypes RT 
	where AR.primaryID = PA.id and AR.secondaryid = SA.id and AR.typeid = RT.id and SA.Id = :assetID order by 3
	"""

taxonomiaSQL = """
	select A.id assetID, A.name assetName, CT.displaysingular categoryTypeName, CS.name categorySuperName, C.name categoryName, C.id categoryID 
	from soaoer.assetcategorizations AC, soaoer.assets A, soaoer.categorizations C, soaoer.categorizations CS, soaoer.categorizationtypes CT 
	where AC.assetid = A.id and AC.catid = C.id and C.typeid = CT.id and C.superid = CS.id and A.id = :assetID 
	union 
	select A.id assetID, A.name assetName, CT.displaysingular categoryTypeName, null categorySuperName, C.name categoryName, C.id categoryID  
	from soaoer.assetcategorizations AC, soaoer.assets A, soaoer.categorizations C, soaoer.categorizationtypes CT 
	where AC.assetid = A.id and AC.catid = C.id and C.typeid = CT.id and C.superid is null and A.id = :assetID order by 2 
	"""

camposSQL = """
	select AXIM.fieldname fieldName, AXI.stringvalue value, AXIM.id 
	from  soaoer.assetxmlindex AXI, soaoer.assetxmlindexmappings AXIM 
	where AXIM.id = AXI.fieldid
	and   AXI.assetid = :assetID
	order by 3
	"""

f = open(os.path.join(os.getcwd(), 'tmp', 'oer-contents.txt'), 'w')

con = cx_Oracle.connect('mgomez/mgomez@oer.vtr.cl/orcl')
cur = con.cursor()
cur.prepare(assetsSQL)
cur.execute(None)

currentAssetFunction = ''

base_wiki_url = 'http://oer.vtr.cl:8080/OERWiki'

for row in cur:

	# Encabezado Asset
	assetID = row[0]
	assetRawName = row[1]
	assetDomainName = row[7]
	assetContextName = row[8]
	assetShortName = row[9]  + ' v' + row[2] + ' (' + row[4] + ')'
	print ("--->" + assetRawName)

	# Lecturas Iniciales

	# Codigo de Integracion
	integration_code = None

	# Descripcion de asset
	asset_description = None

	# Sistema proveedor
	provider_system = None

	# Endpoint
	service_endpoint = None

	# Campos complementarios
	seccion_complementaria = ""
	curCampos = con.cursor()
	curCampos.prepare(camposSQL)
	curCampos.execute(None, {'assetID': assetID})
	for rowCampo in curCampos:
		fieldName = rowCampo[0]
		fieldValue = rowCampo[1]
		if fieldValue != None:
			if fieldName == '/custom-data/integration-code':
				integration_code = fieldValue
			if fieldName == '/custom-data/functional-description':
				asset_description = fieldValue
			if fieldName.startswith('/custom-data/external-systems'):
				provider_system = fieldValue
			if fieldName.startswith('/custom-data/uri/uri/endpoint'):
				service_endpoint = fieldValue

			seccion_complementaria = seccion_complementaria + '  **' + fieldName.replace('/custom-data/', '') + '** ' + fieldValue + '\n\n'

	curCampos.close()

	namePartition = assetRawName.partition('{')[2].partition('}')
	assetDomain = namePartition[0]
	assetSimpleName = namePartition[2]

	if assetSimpleName == '':
		assetSimpleName = assetRawName

	if assetSimpleName == '':
		assetSimpleName = 'Asset id ' + assetID

	assetName = assetSimpleName + ' v' + row[2] + ' (' + row[4] + ')'
	assetType = row[5]
	assetTypeName = row[4]
	assetFunctionName = row[6]

	print ('===>', assetName) 

	if assetType == 196 or assetType == 193 or assetType == 154 or assetType == 50000 or assetType == 50204:
		if currentAssetFunction != assetFunctionName:
			f.write('\n\n' + assetFunctionName + '\n=============================================================================\n')
			currentAssetFunction = assetFunctionName
			currentAssetContext = ""

		if currentAssetContext != assetContextName:
			f.write('\n\n' + assetContextName + '\n------------------------------------------------------------------------------\n')
			currentAssetContext = assetContextName

		f.write('\n\n  :doc:' + '`oer-contents/oer-' + str(assetID) + '`\n\n')
		summary = ""
		if integration_code is not None:
			summary = summary + "**Codigo Integracion**: " + integration_code + "   "

		if provider_system is not None:
			summary = summary + "**Sistema Proveedor**: " + provider_system + "   "
		if summary != "":
			f.write('      ' + summary + '\n\n')

		if asset_description is not None:
			f.write('      ' + asset_description + '\n')

	sf = open(os.path.join('build-rst', 'oer-contents', 'oer-' + str(assetID) + '.rst'), 'w')
	sf.write('.. _oer-' + str(assetID) + '\n')
	sf.write('.. index:: ' + assetName + '\n')
	sf.write('\n\n')
	sf.write(assetShortName + '\n')
	sf.write('-----------------------------------------------------------------------------\n')

	sf.write('\nPara comentarios y observaciones |wiki_link| .\n\n')
	sf.write('.. |wiki_link| raw:: html \n\n') 
	sf.write('   <a href="' + base_wiki_url + '/oer-' + str(assetID) + '-' + assetSimpleName + '" target="_blank">edite la pagina de Wiki</a>\n\n')
	
	if assetDomain != '':
		sf.write('Dominio: ' + assetDomain + '\n\n')

	sf.write('**Oracle Enterprise Repository**. Informacion extraida el ' + time.strftime('%b %d, %Y %H:%M') + '\n\n')
	sf.write('Descripcion\n===============\n')
	if not row[3] is None:
		sf.write(row[3].read() + '\n')
	else:
		if not asset_description is None:
			sf.write(asset_description)
		else:
			sf.write('(Sin Descripcion)')

	# Endpoint
	if service_endpoint is not None:
		sf.write('\n\n.. index:: \n')
		sf.write('   ' + service_endpoint + '\n\n')
		sf.write('\n\nEndpoint\n========\n\n')
		sf.write('  ' + service_endpoint)


	# Codigo de Integracion
	if integration_code is not None:

		sf.write('\n\n.. index:: \n')
		sf.write('   ' + integration_code + '\n\n')
		sf.write('Codigo de Integracion\n========\n\n')
		sf.write('  ' + integration_code)

	# Sistema Proveedor
	if provider_system is not None:
		sf.write('\n\nSistema Proveedor\n========\n\n')
		sf.write('  ' + provider_system)


	# Taxonomia
	curTaxonomia = con.cursor()
	curTaxonomia.prepare(taxonomiaSQL)
	curTaxonomia.execute(None, {'assetID': assetID})
	sf.write('\n\nTaxonomia\n=============\n')
	for rowTaxonomia in curTaxonomia:
		categoryTypeName = rowTaxonomia[2]
		categorySuperName = rowTaxonomia[3]
		categoryName = rowTaxonomia[4]
		if categorySuperName == None:
			sf.write('  **' + categoryTypeName + '** ' + categoryName + '\n\n')
		else:
			sf.write('  **' + categoryTypeName + '** ' + categorySuperName + ': ' + categoryName + '\n\n')

	if curTaxonomia.rowcount == 0:
		sf.write('  No hay datos de taxonomia')

	curTaxonomia.close()

	# Campos complementarios
	sf.write('\n\nInfo Complementaria\n=====================\n')
	if not seccion_complementaria == "":
		sf.write(seccion_complementaria)
	else:
		sf.write('  No hay info complementaria')

	# Proyectos asociados
	curProyectos = con.cursor()
	curProyectos.prepare('select P.name, P.startDate, P.endDate from soaoer.projectsassets PA, soaoer.projects P where PA.projectId = P.Id and PA.assetId = :assetID')
	curProyectos.execute(None, {'assetID': assetID})
	sf.write('\n\nProyectos\n=============\n')
	for rowProyecto in curProyectos:
		sf.write('  ' + rowProyecto[0] + '\n')

	if curProyectos.rowcount == 0:
		sf.write('  No hay proyectos asociados')

	curProyectos.close()

	# Keywords asociados
	curKeywords = con.cursor()
	curKeywords.prepare('select K.keyword from soaoer.assetkeywords K where K.assetId = :assetID')
	curKeywords.execute(None, {'assetID': assetID})
	keywordList = ''
	separator = ''
	for rowKeyword in curKeywords:
		sf.write('\n\n.. index:: \n')
		sf.write('   ' + rowKeyword[0] + '\n\n')
		keywordList = keywordList + separator + rowKeyword[0]
		separator = '; '
	
	sf.write('\n\nKeywords\n========\n\n')
	sf.write('  ' + keywordList)

	if curKeywords.rowcount == 0:
		sf.write('  No hay keywords asociadas')

	curKeywords.close()

	# Archivos relacionados

	sf.write('\n\nArchivos asociados\n=================\n\n')
	curArchivos = con.cursor()
	curArchivos.prepare('select nvl(F.name, F.description) nombre, F.location ubicacion from soaoer.files F, soaoer.assetfiles AF where AF.fileid = F.id and AF.assetid = :assetID')
	curArchivos.execute(None, {'assetID': assetID})
	for rowArchivo in curArchivos:
		sf.write('  ' + rowArchivo[0] + ' ' + rowArchivo[1] + '\n\n')

	if curArchivos.rowcount == 0:
		sf.write('  No hay archivos asociados\n')

	# Artefactos Relacionados
	sf.write('\n\nArtefactos relacionados\n================\n\n')
	curRelacionados = con.cursor()

	curRelacionados.prepare(relacionadosSQL)
	curRelacionados.execute(None, {'assetID': assetID})
	for rowRelacionado in curRelacionados:
		relatedAssetID = rowRelacionado[0]
		sf.write('  ' + rowRelacionado[2] + ' :doc:`oer-' + str(relatedAssetID) + '`\n\n')

	if curRelacionados.rowcount == 0:
		sf.write('  No hay artefactos relacionados\n')

	curRelacionados.close()	



	sf.write('\n\n')
	sf.close()

cur.close()
con.close()
f.close()

