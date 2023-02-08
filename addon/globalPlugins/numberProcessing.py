# -*- coding: UTF-8 -*-
# NumberProcessing
# A global plugin for NVDA
# Copyright 2019 Alberto Buffolino, released under GPL
# Add-on to read digit by digit any number of specified length
# from an experimental idea of Derek Riemer
from gui import guiHelper, nvdaControls
from logHandler import log
from scriptHandler import getLastScriptRepeatCount
from versionInfo import version_year, version_major
import addonHandler
import config
import globalPluginHandler
import globalVars
import gui
import os
import re
import speechDictHandler
import ui
import wx
try:
	from globalCommands import SCRCAT_SPEECH
except:
	SCRCAT_SPEECH = None

addonDir = os.path.join(os.path.dirname(__file__), "..")
if isinstance(addonDir, bytes):
	addonDir = addonDir.decode("mbcs")
curAddon = addonHandler.Addon(addonDir)
addonSummary = curAddon.manifest['summary']

addonHandler.initTranslation()

CURRENCY_SYMBOLS = (
	"$",
	"💵",
	"€",
	"💶",
	"£",
	"💷",
	"¥",
	"💴",
)
confspec = {
	"autoEnable": "boolean(default=false)",
	"prevEnabled": "boolean(default=false)",
	"userMinLen": "integer(default=2)",
}
config.conf.spec["numberProcessing"] = confspec
backupProcessText = speechDictHandler.processText
visitedProfiles = set()
globalEnabled = False
nvdaVersion = '.'.join([str(version_year), str(version_major)])
lastProfile = None

def compileExps():
	basePattern = r'\d{%s,}'%userMinLen
	exp1 = re.compile(basePattern)
	symbols = ''.join(CURRENCY_SYMBOLS)
	exp2 = re.compile(r'([%s]\s*)(%s)'%(symbols, basePattern))
	return (exp1, exp2,)

# (re)load config
def loadConfig():
	global myConf, autoEnable, prevEnabled, userMinLen, exp1, exp2
	myConf = config.conf["numberProcessing"]
	autoEnable = myConf["autoEnable"]
	prevEnabled = myConf["prevEnabled"]
	userMinLen = myConf["userMinLen"]
	exp1, exp2 = compileExps()

loadConfig()

def replaceFunc1(match):
	fixedText = '  '.join(list(match.group(0)))
	return fixedText

def replaceFunc2(match):
	fixedText = '  '.join([*list(match.group(2)), match.group(1)])
	return fixedText

def newProcessText(text):
	text = backupProcessText(text)
	currencyMatch = exp2.match(text)
	if currencyMatch:
		endPos = currencyMatch.span(currencyMatch.lastindex)[1]
		part1 = exp2.sub(replaceFunc2, text[0:endPos])
		part2 = exp1.sub(replaceFunc1, text[endPos:])
		newText = ''.join([part1, part2])
	else:
		newText = exp1.sub(replaceFunc1, text)
	return newText

def enableProcessing():
	global prevEnabled, myConf, globalEnabled
	speechDictHandler.processText = newProcessText
	if autoEnable:
		prevEnabled = myConf["prevEnabled"] = True
	else:
		globalEnabled = True

def disableProcessing():
	global prevEnabled, myConf, globalEnabled
	speechDictHandler.processText = backupProcessText
	if autoEnable:
		prevEnabled = myConf["prevEnabled"] = False
	else:
		globalEnabled = False

# for settings presentation compatibility
if hasattr(gui.settingsDialogs, "SettingsPanel"):
	superDialogClass = gui.settingsDialogs.SettingsPanel
else:
	superDialogClass = gui.SettingsDialog

class NumberProcessingSettingsDialog(superDialogClass):
	"""Class to define settings dialog."""

	if hasattr(gui.settingsDialogs, "SettingsPanel"):
		# Translators: title of settings dialog
		title = _("Number Processing")
	else:
		# Translators: title of settings dialog
		title = _("Number Processing Settings")

	# common to dialog and panel
	def makeSettings(self, settingsSizer):
		loadConfig()
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: label for autoEnable  checkbox in settings
		autoEnableText = _("Processing automatically enabled")
		self.autoEnableCheckBox = settingsSizerHelper.addItem(wx.CheckBox(self, label=autoEnableText))
		self.autoEnableCheckBox.SetValue(myConf["autoEnable"])
		# Translators: label for userMinLen checkbox in settings
		userMinLenLabelText = _("Minimum number of digits to process individually")
		self.userMinLenEdit = settingsSizerHelper.addLabeledControl(
			userMinLenLabelText,
			nvdaControls.SelectOnFocusSpinCtrl,
			min=2,
			initial=myConf["userMinLen"])

	# for dialog only
	def postInit(self):
		self.autoEnableCheckBox.SetFocus()

	# shared between onOk and onSave
	def saveConfig(self):
		# Update Configuration
		prevAutoEnable = myConf["autoEnable"]
		myConf["autoEnable"] = self.autoEnableCheckBox.IsChecked()
		myConf["userMinLen"] = self.userMinLenEdit.GetValue()
		# update global variables
		loadConfig()
		if autoEnable:
			#log.info("autoEnable after configuration")
			enableProcessing()
		elif prevAutoEnable and prevEnabled:
			#log.info("Fix status to avoid manual enabled at first script invocation")
			global globalEnabled
			globalEnabled = True

	# for dialog only
	def onOk(self, evt):
		self.saveConfig()
		super(NumberProcessingSettingsDialog, self).onOk(evt)

	# for panel only
	def onSave(self):
		self.saveConfig()

class QuickSettingsDialog(wx.Dialog):

	def __init__(self, parent, profileName):
		if profileName is None:
			profileName = _("normal configuration")
		title = ' - -'.join([_("Number Processing Settings"), profileName])
		super(QuickSettingsDialog, self).__init__(parent, title=title)
		loadConfig()
		sizerHelper = guiHelper.BoxSizerHelper(self, wx.VERTICAL)
		# Translators: label for userMinLen edit box in settings
		userMinLenLabelText = _("Minimum number of digits to process individually")
		self.userMinLenEdit = sizerHelper.addLabeledControl(
			userMinLenLabelText,
			nvdaControls.SelectOnFocusSpinCtrl,
			min=2,
			initial=myConf["userMinLen"])
		sizerHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
		self.userMinLenEdit.SetFocus()

	def onOk(self, evt):
		# Update Configuration
		myConf["userMinLen"] = self.userMinLenEdit.GetValue()
		# update global variables
		loadConfig()
		self.Destroy()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	scriptCategory = addonSummary

	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		if globalVars.appArgs.secure:
			return
		self.createMenu()
		loadConfig()
		if hasattr(config, "post_configProfileSwitch"):
			config.post_configProfileSwitch.register(self.handleConfigProfileSwitch)
		if autoEnable:
			#log.info("autoEnable at start")
			enableProcessing()

	def createMenu(self):
		# Dialog or the panel.
		if hasattr(gui.settingsDialogs, "SettingsPanel"):
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(NumberProcessingSettingsDialog)
		else:
			self.prefsMenu = gui.mainFrame.sysTrayIcon.menu.GetMenuItems()[0].GetSubMenu()
			# Translators: menu item in preferences
			self.NumberProcessingItem = self.prefsMenu.Append(wx.ID_ANY, _("Number Processing Settings..."), "")
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda e: gui.mainFrame._popupSettingsDialog(NumberProcessingSettingsDialog), self.NumberProcessingItem)

	def terminate(self):
		if hasattr(gui.settingsDialogs, "SettingsPanel"):
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(NumberProcessingSettingsDialog)
		else:
			try:
				self.prefsMenu.RemoveItem(self.NumberProcessingItem)
			except wx.PyDeadObjectError:
				pass
		loadConfig()
		disableProcessing()

	def script_toggleDigitManager(self, gesture, repeating=False):
		if getLastScriptRepeatCount() and not repeating:
			self.launchQuickSettings()
			self.script_toggleDigitManager(None, repeating=True)
			return
		loadConfig()
		if (autoEnable and not prevEnabled) or (not autoEnable and not globalEnabled):
			#log.info("manual enabled")
			enableProcessing()
			message = _("Digit processing on")
		else:
			#log.info("manual disabled")
			disableProcessing()
			message = _("Digit processing off")
		if not repeating:
			ui.message(message)

	script_toggleDigitManager.__doc__ = _("Pressed once, enables/disables digit processing; twice, launches quick settings")

	def launchQuickSettings(self):
		def run():
			gui.mainFrame.prePopup()
			d = QuickSettingsDialog(None, config.conf.profiles[-1].name)
			if d:
				d.Show()
			gui.mainFrame.postPopup()
		wx.CallAfter(run)

	def handleConfigProfileSwitch(self):
		global curProfile
		loadConfig()
		profileName = config.conf.profiles[-1].name
		lastProfile = profileName
		if autoEnable and profileName not in visitedProfiles:
			visitedProfiles.add(profileName)
			#log.info("autoEnable in %s for first time"%profileName)
			enableProcessing()
		elif (autoEnable and prevEnabled) or (not autoEnable and globalEnabled):
			#log.info("enable after changing profile")
			enableProcessing()
		else:
			#log.info("disable after changing profile")
			disableProcessing()

	def event_foreground(self, obj, nextHandler):
		if nvdaVersion < '2018.3':
			curProfile = config.conf.profiles[-1].name
			if lastProfile != curProfile:
				self.handleConfigProfileSwitch()
		nextHandler()

	__gestures = {
		"kb:NVDA+shift+l": "toggleDigitManager"
	}
