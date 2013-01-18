# DefaultTexturesSGFilter DefaultShadingGroupsFilter DefaultShadingGroupsAndMaterialsFilter DefaultAllShadingNodesFilter
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om

import os.path
from Tkinter import Tk
from functools import partial


print os.path.dirname(__file__)


def getAllRegisteredSurfaceShader():
	registeredSurfaceShaders = []
	registeredNodeTypes = cmds.ls(nodeTypes = 1)
	for registeredNodeType in registeredNodeTypes:
		classifications = cmds.getClassification(registeredNodeType)
		for classification in classifications:
			if 'shader/surface' in classification:
				registeredSurfaceShaders.append(registeredNodeType)
	registeredSurfaceShaders = tuple(registeredSurfaceShaders)
	return registeredSurfaceShaders





def createSurfaceShaderItemFilter():
	filterText = 'bpj_SurfaceShaderFilter'

	registeredFilters = cmds.itemFilter(q = 1, listOtherFilters = 1)
	if registeredFilters:
		for registeredFilter in registeredFilters:
			registeredFilterText = cmds.itemFilter(registeredFilter, q = 1, text = 1)
			# print ('%s --> %s' %(registeredFilter, registeredFilterText))
			if registeredFilterText == filterText:
				cmds.delete(registeredFilter)

	filter = cmds.itemFilter(text = filterText, secondScript = 'bpj_createSurfaceShaderItemFilterFunction')

	return filter





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class Ui
#
class Ui(object):

	windowId = ''
	toolbarId = ''
	mainLayout = '' # this layout is holding the whole layout and is getting parented to windows and panels etc
	listLayoutId = ''
	autoRefreshCkbx = ''
	refreshBtn = ''
	sjSelChangeId = ''
	nodeListLayout = None
	mainTabLayout = ''
	shaderTextureDict = ''
	toolbarWidth = 0
	autoRefreshState = 1

	def __init__(self):
		mel.eval("source \"AEfileTemplate.mel\";")
		self.windowId = 'bpj_shaderAndTextureListerWindow'
		self.toolbarId = 'bpj_shaderAndTextureListerToolbar'
		self.listLayoutId = 'bpj_shaderAndTextureListerFormId'
		# self.toolbarWidth = 280
		self.toolbarWidth = 68

		# creating a scriptedPanelType
		if cmds.scriptedPanelType('bpj_shaderAndTextureListerScriptedPanelType', exists = 1) == 0:
			cmds.scriptedPanelType( 'bpj_shaderAndTextureListerScriptedPanelType', unique=True,
				createCallback = 'bpj_shaderAndTextureListerCreateCallback',
				initCallback = 'bpj_shaderAndTextureListerInitCallback',
				addCallback = 'bpj_shaderAndTextureListerAddCallback',
				removeCallback = 'bpj_shaderAndTextureListerRemoveCallback',
				deleteCallback = 'bpj_shaderAndTextureListerDeleteCallback',
				saveStateCallback ='bpj_shaderAndTextureListerSaveStateCallback'
				)

		#  creating an unparented scripted panel
		if cmds.scriptedPanel('bpj_shaderAndTextureListerScriptedPanel', exists = 1):
			cmds.deleteUI('bpj_shaderAndTextureListerScriptedPanel', panel = 1)

		cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel',
			unParent = 1,
			type = 'bpj_shaderAndTextureListerScriptedPanelType',
			menuBarVisible = 0,
			label = 'Shader/Texture Lister'
			)

		# docking to specified position in the maya ui
		# we need to add storing the position in the maya settings and restore the position on maya start
		# self.dockTo(uiPos)

	def dockTo(self, location = None, arg = None):
		self.toolbarWidth = 280
		if location == 'window':
			mel.eval('panelTearOff(\"scriptedPanel", \"bpj_shaderAndTextureListerScriptedPanel\")')
		else:
			# is the lister docked in the viewpanes?
			panels = []
			panels.extend(cmds.paneLayout('viewPanes', q = 1, childArray = 1))
			if len(panels) > 1:
				for panel in panels:
					if panel == 'bpj_shaderAndTextureListerScriptedPanel' and cmds.layout(self.mainLayout, q = 1, isObscured = 1) == 0:
						mel.eval('panelTearOff(\"scriptedPanel", \"bpj_shaderAndTextureListerScriptedPanel\")')
						cmds.window('bpj_shaderAndTextureListerScriptedPanelWindow', e = 1, toolbox = 1, resizeToFitChildren = 0, sizeable = 1)
						# curPanel = cmds.getPanel(withFocus = 1)
						# if curPanel != "":
							# cmds.scriptedPanel("bpj_shaderAndTextureListerScriptedPanel", edit = 1, rp = 'modelPanel1')
					# if panel == 'bpj_shaderAndTextureListerScriptedPanel' and cmds.layout(self.mainLayout, q = 1, isObscured = 1) == 1:

			# is the lister tornOff in a window?
			# fullUiPath = cmds.layout(self.mainLayout, q = 1, fullPathName = 1)
			# fullUiPathList = fullUiPath.split('|')

			# now creating the dockable toolbar
			# mel.eval('panelTearOff(\"scriptedPanel", \"bpj_shaderAndTextureListerScriptedPanel\")')
			# cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel', e = 1, unParent = 1)

			# toolbarWindow = self.createToolbarWindow()

			cmds.window('bpj_shaderAndTextureListerScriptedPanelWindow', edit = True, resizeToFitChildren = True)
			allowedAreas = ['left', 'right', 'top', 'bottom']
			if cmds.toolBar(self.toolbarId, q = 1, exists = 1):
				cmds.deleteUI(self.toolbarId, layout = 1)
			cmds.toolBar( self.toolbarId, area=location, content = 'bpj_shaderAndTextureListerScriptedPanelWindow', allowedArea = allowedAreas, label = 'Shader/Texture Lister' )
			

			# cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel', e = 1, unParent = 1)
			# cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel', e = 1, parent = 'toolbarWindow')

			# if fullUiPathList[0] == 'bpj_shaderAndTextureListerScriptedPanelWindow':
				# cmds.deleteUI('bpj_shaderAndTextureListerScriptedPanelWindow', window = 1)

		self.updateUiOnSelectionChange(self.listLayoutId)
		self.sjSelChangeId = self.createScriptJob()

	def createToolbarWindow(self):
		if cmds.toolBar(self.toolbarId, q = 1, exists = 1):
			cmds.deleteUI(self.toolbarId, layout = 1)

		if cmds.window(self.windowId, q = 1, exists = 1):
			cmds.deleteUI(self.windowId, window = 1)

		# cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel', e = 1, unParent = 1)
		# cmds.scriptedPanel( 'bpj_shaderAndTextureListerScriptedPanel', e = 1, parent = self.windowId)
		# cmds.paneLayout(configuration = 'vertical2')

		cmds.window(self.windowId, title = 'Shader/texture list', toolbox = 1, resizeToFitChildren = 0, sizeable = 1, menuBar = 1, retain = 1)
		return cmds.columnLayout()


	def createUi(self, parent):
		self.mainLayout = cmds.formLayout(parent = parent)
		headerUiLayout = self.createHeaderUi() # create the top buttons
		cmds.setParent('..')

		self.mainTabLayout = cmds.tabLayout(changeCommand = self.onTabChange)
		
		self.nodeListLayout = NodeListLayout() # create the node list layout
		self.listLayoutId = self.nodeListLayout.getId()
		cmds.setParent('..')
		
		allShaders = cmds.columnLayout()
		cmds.button()
		cmds.setParent('..')
		
		allTextures = cmds.columnLayout()
		cmds.button()
		cmds.setParent('..')
		
		cmds.formLayout(
			self.mainLayout,
			edit = 1,
			width = self.toolbarWidth,
			attachForm = [
				# (self.listLayoutId, 'left', 0), 
				# (self.listLayoutId, 'right', 0), 
				# (self.listLayoutId, 'bottom', 0), 
				(self.mainTabLayout, 'left', 0),
				(self.mainTabLayout, 'right', 0),
				(self.mainTabLayout, 'bottom', 0),
				(headerUiLayout, 'left', 0), 
				(headerUiLayout, 'right', 0),
			],
			attachControl = [
				(self.mainTabLayout, 'top', 0, headerUiLayout),
				# (self.listLayoutId, 'top', 0, headerUiLayout),
			],
		)
		
		cmds.tabLayout(
			self.mainTabLayout, 
			edit = True, 
			tabLabel = (
				(self.listLayoutId, 'Inspector'),
				(allShaders, 'Shaders'),
				(allTextures, 'Textures'), 
			),
		)

		self.updateUiOnSelectionChange(self.listLayoutId)
		self.sjSelChangeId = self.createScriptJob()

	def createScriptJob(self):
		cmds.scriptJob(killWithScene = 0, parent = self.mainLayout, event = ['SelectionChanged', self.autoRefreshNodeList])
		# cmds.scriptJob(killWithScene = 0, parent = self.mainLayout, event = ['NameChanged', 'print "Node Rename Triggered!"'])

	def createHeaderUi(self):
		headerUiLayout = cmds.rowColumnLayout(numberOfRows = 1)

		mainMenuBtn = cmds.iconTextButton(label = 'Menu', style = 'iconOnly', image = 'freeformOff.png')
		relAllTexBtn = cmds.iconTextButton(label = ' Rel Tex ', style = 'textOnly', c = self.onReloadTexturesPressed)
		dockBtn = cmds.iconTextButton(label = ' Dock To ', style = 'textOnly')
		self.refreshBtn = cmds.iconTextButton(label = ' Refresh ', style = 'textOnly', c = self.manualRefreshNodeList)
		self.autoRefreshCkbx = cmds.iconTextCheckBox(label = ' Auto Refresh ', value = 1, style = 'textOnly', changeCommand = self.onAutoRefreshCkbxPressed)
		self.menuDockTo(dockBtn)
		self.menuMainMenu(mainMenuBtn)

		cmds.iconTextButton(self.refreshBtn, e = 1, enable = not self.isAutoRefresh())

		return headerUiLayout

	def updateUiOnSelectionChange(self, arg = None):
		self.shaderTextureDict = getShadingGroupsAndTextures()
		self.nodeListLayout.removeAllItems()

		if self.shaderTextureDict:
			for sg in self.shaderTextureDict.keys():
				shader = getShaderFromSg(sg)[0]
				self.nodeListLayout.addItem(shader, 'shader')

				for texture in self.shaderTextureDict[sg]:
					self.nodeListLayout.addItem(texture, 'file')

			# listItems = []
			# listItems = self.nodeListLayout.getAllItems()
			# for item in listItems:
				# print item.node.name()
			# self.nodeListLayout.filterListByType('shader/surface')
			# self.nodeListLayout.filterListByType('file')

	def autoRefreshNodeList(self, arg = None):
		if cmds.window(self.windowId, q = 1, exists = 1):
			if self.isAutoRefresh() == 1 and cmds.window(self.windowId, q = 1, vis = 1) == 1:
				self.updateUiOnSelectionChange()
		elif cmds.layout(self.mainLayout, q = 1, isObscured = 1) == 0:
			if self.isAutoRefresh() == 1:
				self.updateUiOnSelectionChange()

	def manualRefreshNodeList(self, arg = None):
		if cmds.window(self.windowId, q = 1, exists = 1):
			if cmds.window(self.windowId, q = 1, vis = 1) == 1:
				self.updateUiOnSelectionChange()
		elif cmds.layout(self.mainLayout, q = 1, isObscured = 1) == 0:
			self.updateUiOnSelectionChange()

	def menuDockTo(self, parent):
		cmds.popupMenu(button =  1, parent = parent)
		# cmds.menuItem(label = 'Left', c = partial(self.dockTo, 'left'))
		# cmds.menuItem(label = 'Right', c = partial(self.dockTo, 'right'))
		# cmds.menuItem(label = 'Top', c = partial(self.dockTo, 'top'))
		# cmds.menuItem(label = 'Bottom', c = partial(self.dockTo, 'bottom'))
		# cmds.menuItem(divider = 1)
		# cmds.menuItem(label = 'Panel', c = partial(self.dockTo, 'panel'))
		cmds.menuItem(divider = 1)
		cmds.menuItem(label = 'Floating Window', c = partial(self.dockTo, 'window'))

	def menuMainMenu(self, parent):
		cmds.popupMenu(button =  1, parent = parent)
		cmds.menuItem(divider = 1)
		cmds.menuItem(label = 'Production Tools', enable = 0)
		cmds.menuItem(divider = 1)
		cmds.menuItem(label = 'File Texture Manager', c = self.onFileTextureManagerPressed)
		cmds.menuItem(label = 'File Texture Manager Mode', enable = 0)
		cmds.menuItem(label = 'Naming Convention Checker', enable = 0)
		cmds.menuItem(label = 'Batch Resize Textures', enable = 0)
		cmds.menuItem(divider = 1)
		cmds.menuItem(label = 'Settings', enable = 0)
		cmds.menuItem(divider = 1)
		cmds.menuItem(label = 'Help', enable = 0)
		cmds.menuItem(label = 'About', enable = 0)

	def menuShaderLabel(self, parent):
		cmds.popupMenu(button =  1, parent = parent)
		sel = []
		sel = cmds.ls(sl = 1)
		if len(sel) > 0:
			enable = 1
		else:
			enable = 0
		cmds.menuItem(label = 'Assign shader to selection', enable = enable)

	def assignShader(self, shader, arg = None):
		mel.eval('hyperShade -assign ' + shader + ';')

	def onReloadTexturesPressed(self, arg = None):
		logMsg = '--------------------------------------------------------------------------\n'
		if self.shaderTextureDict:
			for sg in self.shaderTextureDict.keys():
				for texture in self.shaderTextureDict[sg]:
					logMsg += str(reloadTexture(texture))
			logMsg += '--------------------------------------------------------------------------\n'
			print logMsg

	def onRefreshBtnPressed(self, arg = None):
		self.updateUiOnSelectionChange()

	def onAutoRefreshCkbxPressed(self, arg = None):
		if self.isAutoRefresh() == 0:
			cmds.iconTextButton(self.refreshBtn, e = 1, enable = 1)
		else:
			cmds.iconTextButton(self.refreshBtn, e = 1, enable = 0)

	def onFileTextureManagerPressed(self, arg = None):
		try:
			mel.eval("source \"FileTextureManager.mel\";FileTextureManager;")
		except:
			cmds.confirmDialog(message = 'Could not find the "File Texture Manager" script!\nIt is either not properly installed, or not installed at all.', title = 'File Texture Manger not found!', button = 'Close')

	def isAutoRefresh(self):
		return cmds.iconTextCheckBox(self.autoRefreshCkbx, q = 1, value = 1)
		
	def onTabChange(self, arg = None):
		selectedTab = cmds.tabLayout(self.mainTabLayout, query = True, selectTabIndex = True)
		tabNameList = cmds.tabLayout(self.mainTabLayout, query = True, tabLabelIndex = True)
		
		print tabNameList[selectedTab-1]
		
		if tabNameList[selectedTab-1] == 'Inspector':
			itemList = self.nodeListLayout.getAllItems()
			for item in itemList:
				print item.getName()

	def switchToPanel(self):
		# fullUiPath = cmds.layout(self.mainLayout, q = 1, fullPathName = 1)
		# fullUiPathList = fullUiPath.split('|')

		curPanel = cmds.getPanel(withFocus = 1)
		if curPanel != "":
			cmds.scriptedPanel("bpj_shaderAndTextureListerScriptedPanel", edit = 1, rp = curPanel)

		# if fullUiPathList[0] == 'bpj_shaderAndTextureListerScriptedPanelWindow':
			# cmds.deleteUI('bpj_shaderAndTextureListerScriptedPanelWindow', window = 1)

	def panelAddCallback(self):
		self.toolbarWidth = 68
		cmds.formLayout( self.mainLayout, e = 1, width = self.toolbarWidth)

		if cmds.toolBar(self.toolbarId, q = 1, exists = 1):
			cmds.deleteUI(self.toolbarId, layout = 1)

		if cmds.window(self.windowId, q = 1, exists = 1):
			cmds.deleteUI(self.windowId, window = 1)

		print self.mainLayout

	def panelRemoveCallback(self):
		if cmds.layout(self.mainLayout, exists = 1):
			cmds.deleteUI(self.mainLayout, layout = 1)





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class NodeListLayout
#
class NodeListLayout(object):

	nodeListLayout = ''
	numberOfColumns = 1
	sortBy = 'name'
	itemList = [] # nodes shown in the NodeListLayout

	def __init__(self):
		self.createLayout()

	def createLayout(self):
		self.nodeListLayout = cmds.scrollLayout(childResizable = 1)

	def addItem(self, node = None, nodeType = None, arg = None):
		if nodeType == 'shader':
			# print 'creating nodelist item %s of type %s' %(node, nodeType)
			self.itemList.append(NodeListItemShader(node, self.nodeListLayout))
		if nodeType == 'file':
			# print 'creating nodelist item %s of type %s' %(node, nodeType)
			self.itemList.append(NodeListItemFile(node, self.nodeListLayout))

	def removeItem(self, node):
		"""
		Input:
			node : nodeHandle
		"""
		print self.itemList[0].node.name()

	def removeItemByListIndex(self, index):
		"""
		Input:
			index int
		"""
		if index > 0 and index <= len(self.itemList):
			cmds.deleteUI(self.getItemByListIndex(index), layout = 1)

	def removeAllItems(self):
		kids = cmds.layout(self.nodeListLayout, q = 1, childArray = 1)

		if kids:
			for kid in kids:
				cmds.deleteUI(kid, layout = 1)

		self.itemList = []

	def getItem(self, node):
		"""
		Input:
			node : nodeHandle
		"""
		pass

	def getItemByListIndex(self, index):
		"""
		Input:
			index int
		"""
		if index > 0 and index <= len(self.itemList):
			return self.itemList[index-1].listItemLayoutId

	def getAllItems(self):
		return self.itemList

	def hideItemByListIndex(self, index):
		cmds.layout(self.getItemByListIndex(index), edit = 1, manage = 0)

	def filterListByType(self, nodeType):
		if len(self.itemList) > 0:
			for item in self.itemList:
				classification = []
				classification.append(item.nodeType)
				classification.extend(cmds.getClassification(item.nodeType))
				clsStr = '|'.join(classification)
				if nodeType in clsStr:
					cmds.layout(item.listItemLayoutId, edit = 1, manage = 1)
				else:
					cmds.layout(item.listItemLayoutId, edit = 1, manage = 0)

	def getId(self):
		return self.nodeListLayout

	def getSortBtn(self):
		pass

	def isEmpty(self):
		if len(self.itemList) == 0:
			return True
		else:
			return False





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class NodeListItem
#
class NodeListItem(object):

	node = None # node handle (MFnDependencyNode)
	nodeType = None
	listItemLayoutId = None
	iconSize = 64
	labelWidth = 180
	bgColor = (0.3, 0.3, 0.3)
	colorCodeError = (0.75, 0, 0)
	colorCodeWarning = (0.75, 0.4, 0)
	colorCodeSuccess = (0, 0.75, 0)

	def __init__(self, nodeStrId, parentLayout):
		"""
		Since we only need one layout to be the container for a list item, we can create this layout
		in the constructor. Its kinda pointless to create a dedicated method (createUi) to do so.
		"""
		self.node = self.getNodeHandle(nodeStrId) # we definitely need some validation here
		self.nodeType = cmds.nodeType(self.node.name())
		# container layout for the NodeListItem
		self.listItemLayoutId = cmds.formLayout(height = self.iconSize, parent = parentLayout)

	def getNodeListLayoutId(self, arg = None):
		pass

	def getNodeHandle(self, nodeStrId):
		selList = om.MSelectionList()
		selList.add(nodeStrId)
		node = om.MObject()
		selList.getDependNode(0, node)

		return om.MFnDependencyNode(node)

	def getName(self):
		return self.node.name()
		
	def updateName(self, arg = None):
		pass

	def getParentLayout(self):
		pass

	def getType(self):
		pass

	def isValid(self):
		pass

	def setColorCode(self):
		if self.isValid():
			print 'Valid'
			
	def update(self, arg = None):
		pass





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class NodeListItemShader
#
class NodeListItemShader(NodeListItem):

	def __init__(self, nodeName, parentLayout):
		NodeListItem.__init__(self, nodeName, parentLayout)
		self.backgroundColor = (0.22, 0.22, 0.22)
		self.createUi()

	def createUi(self):
		nodeStrId = self.node.name()
		swatchCmd = 'mel.eval(\'showEditorExact \"' + nodeStrId + '\";\')'
		shSwatch = cmds.swatchDisplayPort(sn = nodeStrId, wh = (self.iconSize, self.iconSize), renderSize = self.iconSize, pressCommand = swatchCmd)
		shLabel = cmds.iconTextButton(label = nodeStrId, height = self.iconSize, style = 'iconAndTextHorizontal', commandRepeatable = 0, c = 'import bpj_shaderAndTextureLister as satl\nsatl.onShadingNodeLabelPressed("' + nodeStrId + '")')
		shCollapseChkbx = cmds.iconTextButton(label = 'Collapse/Expand', annotation = 'collapse shader', width = 18, height = self.iconSize, style = 'iconOnly', image1 = 'bpj_nodeListItemArrowDown_64.png', commandRepeatable = 0)

		# self.setColorCode()
		cmds.formLayout( self.listItemLayoutId, edit = 1, backgroundColor = self.backgroundColor, annotation = nodeStrId,
			attachForm = [
				(shSwatch, 'left', 0),
				(shCollapseChkbx, 'right', 0),
				(shSwatch, 'top', 0),
				(shLabel, 'top', 0),
				(shCollapseChkbx, 'top', 0),
				],
			attachControl = [
				(shLabel, 'left', 0, shSwatch),
				(shLabel, 'right', 0, shCollapseChkbx)
				])





#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class NodeListItemFile
#
class NodeListItemFile(NodeListItem):

	def __init__(self, nodeName, parentLayout):
		NodeListItem.__init__(self, nodeName, parentLayout)
		self.backgroundColor = (0.3, 0.3, 0.3)
		self.createUi()

	def isValid(self):
		"""
		Override NodeListItem.isValid()
		"""
		from os.path import exists

		filePath = cmds.getAttr(self.node.name() + '.fileTextureName')

		if exists(filePath):
			return True
		else:
			return False

	def createUi(self):
		nodeStrId = self.node.name()
		swatchCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.onShadingNodePressed("' + nodeStrId + '")'
		txSwatch = cmds.swatchDisplayPort(sn = nodeStrId, wh = (self.iconSize, self.iconSize), renderSize = self.iconSize, pressCommand = swatchCmd)
		filePath = cmds.getAttr(nodeStrId + '.fileTextureName')

		if filePath != '':
			label = os.path.basename(filePath)
		else:
			label = 'No file referenced!'

		labelCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.browseForTexture("' + nodeStrId + '")'
		shLabel = cmds.iconTextButton(label = label, height = self.iconSize/2, style = 'iconAndTextHorizontal', commandRepeatable = 0)

		openFileCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.browseForTexture("' + nodeStrId + '")'
		openFileBtn = cmds.iconTextButton(label = 'Load Texture', annotation = 'Browse for a file on your computer...', image1 = 'freeformOff.png', height = self.iconSize/2, width = self.iconSize/2, style = 'iconOnly', commandRepeatable = 0, command = openFileCmd)

		viewFileCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.viewTexture("' + nodeStrId + '")'
		viewFileBtn = cmds.iconTextButton(label = 'View Texture', annotation = 'View texture file with your preferred image viewer', image = 'freeformOff.png', height = self.iconSize/2, width = self.iconSize/2, style = 'iconOnly', commandRepeatable = 0, command = viewFileCmd)

		editFileCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.EditTexture("' + nodeStrId + '")'
		editFileBtn = cmds.iconTextButton(label = 'Edit Texture', annotation = 'Edit texture file with your preferred image editor', image = 'freeformOff.png', height = self.iconSize/2, width = self.iconSize/2, style = 'iconOnly', commandRepeatable = 0, command = editFileCmd)

		openFileLocCmd = 'import bpj_shaderAndTextureLister as satl\nsatl.openTextureLocation("' + nodeStrId + '")'
		msg =  'LMB: Open texture file location in explorer\n'
		msg += 'LMB+Shift: Copy file path to clipboard\n'
		msg += 'LMB+Alt: Copy folder path to clipboard'
		openFileLocBtn = cmds.iconTextButton(label = 'Open Texture Location', annotation = msg, image = 'freeformOff.png', height = self.iconSize/2, width = self.iconSize/2, style = 'iconOnly', commandRepeatable = 0, command = openFileLocCmd)

		cmds.formLayout( self.listItemLayoutId, edit = 1, backgroundColor = self.backgroundColor, annotation = filePath,
			attachForm = [(txSwatch, 'left', 0), (shLabel, 'right', 0)],
			attachControl = [
				(shLabel, 'left', 0, txSwatch),
				(openFileBtn, 'left', 10, txSwatch),
				(openFileBtn, 'top', 0, shLabel),
				(viewFileBtn, 'left', 0, openFileBtn),
				(viewFileBtn, 'top', 0, shLabel),
				(editFileBtn, 'left', 0, viewFileBtn),
				(editFileBtn, 'top', 0, shLabel),
				(openFileLocBtn, 'left', 0, editFileBtn),
				(openFileLocBtn, 'top', 0, shLabel)
				] )





def reloadTexture(fileNode):
	logMsg = ''
	if fileNode:
		import os.path

		filePath = cmds.getAttr(fileNode + '.fileTextureName')

		if os.path.exists(filePath):
			mel.eval("AEfileTextureReloadCmd(\"" + fileNode + '.fileTextureName' + "\");")
			logMsg = 'Reloaded file: %s\n' %filePath
		else:
			if filePath != '':
				logMsg = 'File node "%s" is referencing a file which doesnt exists:%s\n' %(fileNode, filePath)
			else:
				logMsg = 'File node "' + fileNode + '" is not referencing any file!\n'
		return logMsg





def browseForTexture(fileNode):
	if fileNode:
		from os.path import exists
		imageFileFilter = 'Images (*.tga *.png *.jpg *.jpeg *.tif)'
		filePath = cmds.getAttr(fileNode + '.fileTextureName')
		images = cmds.fileDialog2(fileFilter = imageFileFilter, fileMode = 1, startingDirectory = filePath)
		if images != None:
			for image in images:
				melStr = 'AEassignTextureCB "%s.fileTextureName" "%s" ""' %(fileNode, image)
				mel.eval(melStr)





def viewTexture(fileNode):
	# AEfileTextureViewCmd file1.fileTextureName;
	mel.eval("AEfileTextureViewCmd(\"" + fileNode + '.fileTextureName' + "\");")





def EditTexture(fileNode):
	# AEfileTextureEditCmd file1.fileTextureName;
	mel.eval("AEfileTextureViewCmd(\"" + fileNode + '.fileTextureName' + "\");")





def openTextureLocation(fileNode):
	import os.path
	from os import startfile
	filePath = cmds.getAttr(fileNode + '.fileTextureName')
	if filePath != '':
		mods = cmds.getModifiers()
		
		if mods == 0:
			startfile(os.path.dirname(filePath))
			
		if mods == 8: # shift
			r = Tk()
			r.withdraw()
			r.clipboard_clear()
			r.clipboard_append(os.path.dirname(filePath))
			r.destroy()
			
			# return True
			
		if mods == 1: # alt
			r = Tk()
			r.withdraw()
			r.clipboard_clear()
			r.clipboard_append(filePath)
			r.destroy()
			
			# return True





def onShadingNodePressed(shadingNode):
	aeVis = mel.eval('int $bpj_temp = `isUIComponentVisible "Attribute Editor"`;')
	# if aeVis == 0:
	mel.eval('showEditorExact \"' + shadingNode + '\";')
	# else:
		# mel.eval('setUIComponentVisibility "Attribute Editor" 0;')
	# mel.eval('setUIComponentVisibility "Attribute Editor" 1;')

def onShadingNodeLabelPressed(shadingNode):
	mod = cmds.getModifiers()
	if mod == 1: # shift
		mel.eval('hyperShade -assign "' + shadingNode + '";')
	elif mod == 8: # alt
		# TODO: need to check, if the hyperShadePanel1 exists either in a viewport or in a window
		result = ''
		try:
			mel.eval('setFocus "hyperShadePanel1";')
			mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "showBottomTabsOnly");')
			mel.eval('hyperShade -shaderNetwork "' + shadingNode + '";')
			mel.eval('hyperShadePanelGraphCommand("hyperShadePanel1", "rearrangeGraph");')
		except:
			mel.eval('print "Please open the Hypershader first and try again.";')
			result = cmds.confirmDialog(message = 'Please open the Hypershader first and try again.\nSorry, that might be a Maya bug... or maybe not...\nWe will see :)', button = 'Open Hypershader')

		if result == 'Open Hypershader':
			mel.eval('HypershadeWindow;')

	elif mod == 4: # ctrl
		mel.eval('hyperShade -objects "' + shadingNode + '";')





def getShaderFromSg(shadingEngine = ''):
	surfaceShader = cmds.listConnections(shadingEngine + '.surfaceShader', plugs = 0)
	miMaterialShader = cmds.listConnections(shadingEngine + '.miMaterialShader', plugs = 0)

	if surfaceShader != None:
		return surfaceShader
	elif miMaterialShader != None:
		return miMaterialShader
	else:
		return None






def getShadingGroupsAndTextures():
	# shading engines connected to compInstObjGroups[n].compObjectGroups[n] are usually
	# not assigned to the mesh anymore.
	# How to recreate this case:
	# - create a mesh (default lambert shader is assigned (initalShadingGroup))
	# - switch to face comp mode and select ALL faces
	# - assign a new shader to the selected faces
	# Use the listHistory or listConnections (type = 'shadingEngine') command to see the
	# initialShadingGroup still being listed as connected to the mesh
	# while its not assigned to the mesh at all anymore
	# sel = cmds.ls(sl = 1, long = 0, shapes = 1, dag = 1, noIntermediate = 1, type = ('mesh', 'nurbsSurface', 'subdiv'))
	sel = cmds.ls(sl = 1, long = 0, shapes = 1, dag = 1, noIntermediate = 1)

	# TODO:
	# creating a itemFilter for use with the lsThroughFilter
	# command to get rid of all non surfaceShape nodes
	surfaceShapeList = []
	
	validNodes = cmds.ls(sel, type = ['mesh', 'nurbsSurface', 'subdiv'])
	
	if len(validNodes) == 0:
		return None
		
	surfaceShapeList.extend(validNodes)

	shadingEngineList = []
	shaderTextureDict = {}
	fileFilter = cmds.itemFilter(byType = 'file')

	for item in surfaceShapeList:
		connections = cmds.listConnections(item, s = 1, plugs = 1, type = 'shadingEngine', skipConversionNodes = 1)
		if connections:
			for c in connections:
				sourcePlug = cmds.connectionInfo(c, sourceFromDestination = 1)
				if 'compInstObjGroups[' not in sourcePlug:
					shadingEngineList.append(c.split('.')[0])

	shadingEngineList = list(set(shadingEngineList))

	if len(shadingEngineList) > 0:
		for shadingEngine in shadingEngineList:
			nodeList = cmds.listHistory(shadingEngine, future = 0, allGraphs = 1)
			fileNodeList = cmds.lsThroughFilter(fileFilter, item = nodeList, nodeArray = 1, sort = 'byName')
			fileNodeList = list(set(fileNodeList))

			shaderTextureDict[shadingEngine] = fileNodeList

		return shaderTextureDict
	else:
		return None

	cmds.delete(fileFilter)


