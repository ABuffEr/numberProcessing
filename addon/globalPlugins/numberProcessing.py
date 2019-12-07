# -*- coding: UTF-8 -*-
# NumberProcessing
# A global plugin for NVDA
# Copyright 2019 Alberto Buffolino, released under GPL
# Add-on to read digit by digit any number of specified length
# from an experimental idea of Derek Riemer
from gui import guiHelper, nvdaControls
from scriptHandler import getLastScriptRepeatCount
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

confspec = {
"initialState": "boolean(default=false)",
"userMinLen": "integer(default=2)",
}

config.conf.spec["numberProcessing"] = confspec
myConf = config.conf["numberProcessing"]
userMinLen = myConf["userMinLen"]
oldProcessText = None

def compileExp():
	exp = re.compile(r'\d{%s,}'%userMinLen)
	return exp

exp = compileExp()

# (re)load config
def loadConfig():
	global myConf, userMinLen, exp
	myConf = config.conf["numberProcessing"]
	userMinLen = myConf["userMinLen"]
	exp = compileExp()

def replaceFunc(match):
	fixedText = '  '.join(list(match.group(0)))
	return fixedText

def newProcessText(text):
	text = oldProcessText(text)
	newText = exp.sub(replaceFunc, text)
	return newText

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
		# Translators: label for initialState  checkbox in settings
		initialStateText = _("Processing automatically enabled")
		self.initialStateCheckBox = settingsSizerHelper.addItem(wx.CheckBox(self, label=initialStateText))
		self.initialStateCheckBox.SetValue(myConf["initialState"])
		# Translators: label for userMinLen checkbox in settings
		userMinLenLabelText = _("Minimum number of digits to process individually")
		self.userMinLenEdit = settingsSizerHelper.addLabeledControl(
			userMinLenLabelText,
			nvdaControls.SelectOnFocusSpinCtrl,
			min=2,
			initial=myConf["userMinLen"])

	# for dialog only
	def postInit(self):
		self.initialStateCheckBox.SetFocus()

	# shared between onOk and onSave
	def saveConfig(self):
		# Update Configuration
		myConf["initialState"] = self.initialStateCheckBox.IsChecked()
		myConf["userMinLen"] = self.userMinLenEdit.GetValue()
		# update global variables
		loadConfig()

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
		if myConf["initialState"]:
			self.script_toggleDigitManager(None, silent=True)

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
		global oldProcessText
		if oldProcessText:
			speechDictHandler.processText = oldProcessText
			oldProcessText = None

	def script_toggleDigitManager(self, gesture, silent=False, repeating=False):
		if getLastScriptRepeatCount() and not repeating:
			def run():
				gui.mainFrame.prePopup()
				d = QuickSettingsDialog(None, config.conf.profiles[-1].name)
				if d:
					d.Show()
				gui.mainFrame.postPopup()
			wx.CallAfter(run)
			self.script_toggleDigitManager(None, silent=True, repeating=True)
			return
		loadConfig()
		global oldProcessText
		if oldProcessText:
			speechDictHandler.processText = oldProcessText
			oldProcessText = None
			if not silent:
				ui.message(_("Digit processing off"))
		else:
			oldProcessText = speechDictHandler.processText
			speechDictHandler.processText = newProcessText
			if not silent:
				ui.message(_("Digit processing on"))

	script_toggleDigitManager.__doc__ = _("Pressed once, enables/disables digit processing; twice, launches quick settings")

	__gestures = {
		"kb:NVDA+shift+l": "toggleDigitManager"
	}
