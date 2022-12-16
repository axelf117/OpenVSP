import os
import sys

import wx
import time
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor

import numpy as np
import vtk.util.numpy_support as npsup

from pyvsp.user_prop_panel import UserPropertyPanel
from pyvsp.analysis_panel import AnalysisPanel

from threading import Thread
from time import sleep

import socket

import subprocess

import pickle

HOST = "localhost"  # The server's hostname or IP address
PORT = 6000  # The port used by the server


class DemoFrame(wx.Frame):
    """
    The main wxpython frame for the demo app
    Contains 4 main panels
    |---------------------|--------|
    |                     |        |
    |                     |        |
    |                     |   AM   |
    |     vtk_panel       |        |
    |                     |        |
    |                     |        |
    |                     |        |
    |------------------------------|
    |               |              |
    |    blank      |     user     |
    |               |     Parms    |
    |---------------|--------------|
    """
    def __init__(self, make_vtk = False):
        """
        initializes the main demo frame

        Parameters
        ----------
        make_vtk : bool, optional
            Controls whether the vtk panel will be made, by default False
            There are some weird interactions between the vtk panel and OpenVSP
        """
        wx.Frame.__init__(
            self,
            None,
            id=wx.ID_ANY,
            title='test_app',
            pos=wx.DefaultPosition,
            size=wx.Size(1400, 800),
            style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        )

        #creating main layout splitters
        self.vtkPanel = None
        mainSplitter = wx.SplitterWindow(
            self,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D
        )
        top_splitter = wx.SplitterWindow(
            mainSplitter,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D
        )
        bottom_splitter = wx.SplitterWindow(
            mainSplitter,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D
        )



        mainSplitter.SplitHorizontally(top_splitter, bottom_splitter)
        mainSplitter.SetSashGravity(0.75)
        mainSplitter.SetMinimumPaneSize(10)

        #creates the VTK panel
        self.made_vtk = False
        self.vtk_panel_buffer = wx.Panel(top_splitter, -1, style=wx.DOUBLE_BORDER)
        self.vtk_panel_buffer_box = wx.BoxSizer(wx.VERTICAL)
        if make_vtk:
            self.made_vtk = True
            self.vtkPanel = VTK_Panel_Vehicle(self.vtk_panel_buffer)
            self.vtk_panel_buffer_box.Add(self.vtkPanel, 1, wx.EXPAND|wx.ALL,5)
        self.vtk_panel_buffer.SetSizer(self.vtk_panel_buffer_box)

        #creates the analyis panel
        self.analysis_panel = wx.Panel(top_splitter, -1, style=wx.DOUBLE_BORDER)#AnalysisPanel(top_splitter, vsp)

        #adds analysis panel and vtk panel
        top_splitter.SplitVertically(self.vtk_panel_buffer, self.analysis_panel)
        top_splitter.SetSashGravity(0.75)
        top_splitter.SetMinimumPaneSize(10)

        #create button panel
        button_buffer = wx.Panel(bottom_splitter, -1, style=wx.DOUBLE_BORDER)
        button_buffer_box = wx.BoxSizer(wx.VERTICAL)
        self.add_buttons(button_buffer,button_buffer_box)
        button_buffer.SetSizerAndFit(button_buffer_box)

        #create user param panel
        self.prop_panel = wx.Panel(bottom_splitter, -1, style=wx.DOUBLE_BORDER) #UserPropertyPanel(bottom_splitter, vsp)

        #adds button and param panels
        bottom_splitter.SplitVertically(button_buffer, self.prop_panel)
        bottom_splitter.SetSashGravity(0.5)
        bottom_splitter.SetMinimumPaneSize(10)

        #renders vtk screen
        if self.made_vtk:
            self.vtkPanel.renderVTKScreen()

        #adds filemenu
        self.add_menu_bar()

        #finishes layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(mainSplitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

        #setting variables
        self.did_init_gui = False
        self.sock = None

    def add_menu_bar(self):
        """
        Adds menu bar and file menu
        """
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()

        load_model = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Load Model', wx.EmptyString, wx.ITEM_NORMAL)
        file_menu.Append(load_model)
        self.Bind(wx.EVT_TOOL, self.on_load_model, load_model)

        save_model = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Save Model', wx.EmptyString, wx.ITEM_NORMAL)
        file_menu.Append(save_model)
        self.Bind(wx.EVT_TOOL, self.on_save_model, save_model)

        close_model = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Close Model', wx.EmptyString, wx.ITEM_NORMAL)
        file_menu.Append(close_model)
        self.Bind(wx.EVT_TOOL, self.on_close_model, close_model)

        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

    def add_buttons(self, button_buffer, button_buffer_box):
        """
        Adds buttons to the button box

        Parameters
        ----------
        button_buffer : wx.Panel
            The panel containing the button buffer box
        button_buffer_box : wx.BoxSizer
            the boxsizer to contain the buttons
        """
        edit_model = wx.Button(button_buffer, wx.ID_ANY, u"Edit Model", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_BUTTON, self.on_edit_model, edit_model)
        button_buffer_box.Add(edit_model)

        refresh_model = wx.Button(button_buffer, wx.ID_ANY, u"Refresh Model", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_BUTTON, self.on_refresh_model, refresh_model)
        button_buffer_box.Add(refresh_model)

        run_automated_script = wx.Button(button_buffer, wx.ID_ANY, u"Run Automated Script", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_BUTTON, self.on_run_automated_script, run_automated_script)
        button_buffer_box.Add(run_automated_script)

        # start_openvsp = wx.Button(button_buffer, wx.ID_ANY, u"Init OpenVSP GUI", wx.DefaultPosition, wx.DefaultSize, 0)
        # self.Bind(wx.EVT_BUTTON, self.on_start_openvsp, start_openvsp)
        # button_buffer_box.Add(start_openvsp)

        start_server = wx.Button(button_buffer, wx.ID_ANY, u"Start VSP Server", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_BUTTON, self.on_start_server, start_server)
        button_buffer_box.Add(start_server)

        end_server = wx.Button(button_buffer, wx.ID_ANY, u"End VSP Server", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_BUTTON, self.on_end_server, end_server)
        button_buffer_box.Add(end_server)

        # check_updates = wx.Button(button_buffer, wx.ID_ANY, u"Check VSP for Updates", wx.DefaultPosition, wx.DefaultSize, 0)
        # self.Bind(wx.EVT_BUTTON, self.on_check_updates, check_updates)
        # button_buffer_box.Add(check_updates)

        self.update_count = wx.StaticText(button_buffer, id=wx.ID_ANY, label="-1", pos=wx.DefaultPosition, size=wx.DefaultSize )
        button_buffer_box.Add(self.update_count)

        # switch_to_openvsp = wx.Button(button_buffer, wx.ID_ANY, u"Switch to OpenVSP GUI", wx.DefaultPosition, wx.DefaultSize, 0)
        # self.Bind(wx.EVT_BUTTON, self.on_switch_to_openvsp, switch_to_openvsp)
        # button_buffer_box.Add(switch_to_openvsp)

    def on_start_server(self, event):
        server_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vsp_server.py')
        proc = subprocess.Popen( [sys.executable, server_file] )

        sleep(1)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))

        self.timer = wx.Timer(self)
        self.Bind( wx.EVT_TIMER, self.on_check_updates, self.timer )
        self.timer.Start(1000) # 1 Hz

    def on_end_server(self, event):
        self.sock.sendall(pickle.dumps(['close']))
        self.sock.close()

    def on_check_updates(self, event):
        cnt = self.send_recieve('GetAndResetUpdateCount', [])
        self.update_count.SetLabel( str(cnt) )
        # print( cnt )

    # def on_start_openvsp(self, event):
    #     """
    #     event called to initialize the openvsp gui

    #     Parameters
    #     ----------
    #     event : wx.Event
    #         The button event
    #     """
    #     def start_gui():

    #         print("before start gui")
    #         sleep(1)
    #         vsp.InitGui()
    #         sleep(1)
    #         vsp.StartGui()
    #         print("after start gui")
    #         # event.set()
    #     if self.did_init_gui:
    #         print("init gui already called")
    #         return

    #     print("before thread")
    #     t = Thread(target=start_gui, args=())
    #     t.start()
    #     print("after thread")
    #     self.did_init_gui = True

    # def on_switch_to_openvsp(self, event):
    #     """
    #     event called to switch to the openvsp gui

    #     Parameters
    #     ----------
    #     event : wx.Event
    #         the button event
    #     """
    #     self.Freeze() # weird interactions happen between openvsp and wxpython if not frozen
    #     if self.did_init_gui:
    #         vsp.StartGui()
    #         print("return from vsp gui")
    #         wx.CallAfter(self.vsp_update)
    #     else:
    #         print("need to init gui first")

    #     self.Thaw()

    def on_load_model(self, event):
        """
        event called when the user clicks the load model button

        Pop allows user to select file
        file loaded with vsp API

        Parameters
        ----------
        event : wx.Event
            the button event
        """
        print("load model button clicked")
        if self.is_file_loaded:
            print("File already loaded")
            return
        dlg = wx.FileDialog(self,
                    message="Select an vsp3 or csm file to Import...",
                    defaultFile="",
                    wildcard="OpenVSP (*.vsp3)|*.vsp3;",
                    style=wx.FD_OPEN)
        result = dlg.ShowModal()
        geom_file_path = ""
        if result == wx.ID_OK:
            geom_file_path = dlg.GetPath()
        else:
            return
        dlg.Destroy()
        if geom_file_path != "":
            self.is_open = True
            self.load_vsp(geom_file_path)


    @property
    def is_file_loaded(self):
        """
        bool indicating whether a vsp file is loaded
        """
        # name = vsp.GetVSPFileName()
        name = self.send_recieve('GetVSPFileName',[])
        if name == 'Unnamed.vsp3':
            return False
        return True
    def on_save_model(self, event):
        """
        event called when the user clicks the save model button

        Pop allows user to select save destination
        file saved with vsp API

        Parameters
        ----------
        event : wx.Event
            the button event
        """

        print("save model button clicked")
        if not self.is_file_loaded:
            print("no file loaded")
            return

        dlg = wx.FileDialog(self,
                            message="Save vsp3 file as...",
                            defaultFile="",
                            wildcard="*.vsp3",
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            file_path = dlg.GetPath()
        dlg.Destroy()

        vsp.WriteVSPFile(file_path, vsp.SET_ALL)
        print(f"model saved as {file_path}")

    def on_close_model(self, event):
        """
        event called when the user clicks the close model button

        model cleared from vsp api

        Parameters
        ----------
        event : wx.Event
            the button event
        """

        print("close model button clicked")
        if not self.is_file_loaded:
            print("no model loaded")
            return
        # vsp.ClearVSPModel()
        self.send_recieve('ClearVSPModel',[])

    def on_edit_model(self, event):
        """
        event called when the user clicks the edit model button

        Allows the user to edit the X location value of the first component of an OpenVSP model

        Parameters
        ----------
        event : wx.Event
            the button event
        """

        print("edit model button clicked")
        if not self.is_file_loaded:
            print("no model loaded")
            return

        dlg = wx.TextEntryDialog(self, "Select new X location for component 1", "X Value", "10",)
        if dlg.ShowModal() == wx.ID_OK:
            new_x_value = dlg.GetValue()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        try:
            new_x_value = float(new_x_value)
        except:
            print(f"could not convert {new_x_value} to float")

        # geom_list = vsp.FindGeoms()
        geom_list = self.send_recieve('FindGeoms',[])
        # vsp.SetParmVal(geom_list[0], 'X_Location', 'XForm', new_x_value)
        self.send_recieve('SetParmVal',[geom_list[0], 'X_Location', 'XForm', new_x_value])
        # vsp.Update()
        self.send_recieve('Update', [])
        # vsp.UpdateGui()
        self.send_recieve('UpdateGUI', [])
        # self.refresh_actors()

    def on_refresh_model(self, event):
        """
        event called when the user clicks refresh model button

        ultimetly triggers all cascading "updated from vsp" functions

        Parameters
        ----------
        event : wx.Event
            the button event
        """

        print("refresh model button clicked")
        self.vsp_update()

    def load_vsp(self, geom_file_path):
        """
        function used for loading a vsp file

        Parameters
        ----------
        geom_file_path : str
            file path to the vsp file
        """
        self.dir = os.path.dirname(geom_file_path)
        self.geom_file = os.path.basename(geom_file_path)
        print("Opening OpenVSP file: %s" % self.geom_file)
        # vsp.ReadVSPFile(os.path.join(self.dir, self.geom_file))
        self.send_recieve('ReadVSPFile', [os.path.join(self.dir, self.geom_file)])
        self.vsp_update()

    def vsp_update(self):
        """
        Calls all children vsp updates
        """
        # self.refresh_actors()
        # self.prop_panel.vsp_update()
        # self.analysis_panel.vsp_update()
    def refresh_actors(self):
        """
        updates vtk window
        """
        print("refrehsing view")
        tess_dict = self.make_tesselations()
        if self.made_vtk:
            self.vtkPanel.make_geom_tesselations(tess_dict)
            self.vtkPanel.redraw()
            self.vtkPanel.fitToExtents()

    def on_run_automated_script(self, event):
        """
        event called when user click automated script

        initiates automation script

        Parameters
        ----------
        event : wx.Python
            event
        """
        print("Run Automated Script clicked")
        if not self.is_file_loaded:
            print("no model loaded")
            return
        # self.refresh_actors()
        wx.CallLater(3000, lambda: self.automation(0))

    def automation(self, x):
        """
        automation script

        changes the x value of the first openvsp component
        increments starting value by 10 until it is > 100

        Parameters
        ----------
        x : float
            The starting or previous value of X
        """
        print(f"setting component_1 x_location to {x}")
        # geom_list = vsp.FindGeoms()
        geom_list = self.send_recieve('FindGeoms', [])
        # vsp.SetParmVal(geom_list[0], 'X_Location', 'XForm', x)
        self.send_recieve('SetParmVal', [geom_list[0], 'X_Location', 'XForm', x])
        # vsp.Update()
        self.send_recieve('Update', [])
        # vsp.UpdateGui()
        self.send_recieve('UpdateGui', [])
        # self.refresh_actors()
        x += 10
        if x > 100:
            print("automated script complete")
            return
        wx.CallLater(3000, lambda: self.automation(x))


    def make_tesselations(self,):
        """
        generates tesselations for viewing in VTK

        Returns
        -------
        tess: {geom_id: points}
            a str to list dict
            Each geom id key has a complicated list of points
        """
        # geom_list = vsp.FindGeoms()
        geom_list = self.send_recieve('FindGeoms', [])
        tess = {}
        for geom_id in geom_list:

            # geom_name = vsp.GetGeomName(geom_id)
            # self.geom_ids[geom_name] = geom_id
            # for surf_indx in range(vsp.GetNumMainSurfs(geom_id)):
            for surf_indx in range(self.send_recieve('GetNumMainSurfs', [geom_id])):
                if surf_indx == 0:
                    # if vsp.GetNumMainSurfs(geom_id) > 1:
                    if self.send_recieve('GetNumMainSurfs', [geom_id]) > 1:
                        print("Only one main surface is handled. VSP component \"%s\" has many" % geom_id)
                    tess[geom_id] = self.get_tesselation(geom_id, surf_indx)
        return tess
    def get_tesselation(self, geom_id, surf_indx):
        """
        returns points needed to draw openvsp components

        Parameters
        ----------
        geom_id : str
            an openvsp geom id
        surf_indx : int
            a surface index of the geom_id

        Returns
        -------
        list
            a complicated list of points
        """
        sym = self.get_symmetry(geom_id)
        # u_vec, w_vec = vsp.GetUWTess01(geom_id, surf_indx)
        u_vec, w_vec = self.send_recieve('GetUWTess01', [geom_id, surf_indx])
        u_vec = np.array(u_vec)
        w_vec = np.array(w_vec)
        u_tess, w_tess = np.meshgrid(u_vec, w_vec)
        u_tess = u_tess.flatten()
        w_tess = w_tess.flatten()
        # points = vsp.CompVecPnt01(geom_id, surf_indx, u_tess, w_tess)
        points = self.send_recieve('CompVecPnt01', [geom_id, surf_indx, u_tess, w_tess])
        point_tess = np.empty((len(u_tess),3), dtype=float)
        for i, point in enumerate(points):
            point_tess[i,0] = point.x()
            point_tess[i,1] = point.y()
            point_tess[i,2] = point.z()

        xy_sym = np.empty((0, 0, 3))
        xz_sym = np.empty((0, 0, 3))
        yz_sym = np.empty((0, 0, 3))
        if "XY" in sym:
            xy_sym = np.empty(np.shape(point_tess))
            xy_sym[:, 0] = point_tess[:, 0]
            xy_sym[:, 1] = point_tess[:, 1]
            xy_sym[:, 2] = -point_tess[:, 2]
            xy_sym = xy_sym.reshape((len(u_vec), len(w_vec), 3))
        if "XZ" in sym:
            xz_sym = np.empty(np.shape(point_tess))
            xz_sym[:, 0] = point_tess[:, 0]
            xz_sym[:, 1] = -point_tess[:, 1]
            xz_sym[:, 2] = point_tess[:, 2]
            xz_sym = xz_sym.reshape((len(u_vec), len(w_vec), 3))
        if "YZ" in sym:
            yz_sym = np.empty(np.shape(point_tess))
            yz_sym[:, 0] = -point_tess[:, 0]
            yz_sym[:, 1] = point_tess[:, 1]
            yz_sym[:, 2] = point_tess[:, 2]
            yz_sym = yz_sym.reshape((len(u_vec), len(w_vec), 3))

        return (
            point_tess.reshape((len(u_vec), len(w_vec), 3)),
            [xy_sym, xz_sym, yz_sym]
        )
    def get_symmetry(self, geom_id):
        """
        returns symmetry plane of the openVSP component

        Returns
        -------
        sym_vals : str
            'XY', 'XZ', or 'YZ' symmetry plane
        """

        # sym_val = vsp.GetParmVal(vsp.FindParm(geom_id, "Sym_Planar_Flag", "Sym"))
        sym_val = self.send_recieve('GetParmVal', [self.send_recieve('FindParm', [geom_id, "Sym_Planar_Flag", "Sym"])])
        if sym_val == 0.0:
            return []
        elif sym_val == 1.0:
            return ["XY"]
        elif sym_val == 2.0:
            return ["XZ"]
        elif sym_val == 3.0:
            return ["XY", "XZ"]
        elif sym_val == 4.0:
            return ["YZ"]
        elif sym_val == 5.0:
            return ["XY", "YZ"]
        elif sym_val == 6.0:
            return ["XZ", "YZ"]
        elif sym_val == 7.0:
            return ["XY", "XZ", "YZ"]
        else:
            print("UNKNOWN SYM VALUE FOUND")
            return []
    def send_recieve(self, func_name, args):
        b_data = pickle.dumps([func_name, args])
        print(f"sent data: {[func_name, args]}")
        self.sock.sendall(b_data)
        # b_result = self.sock.recv(1024)
        result = None
        b_result = []
        while True:
            packet = self.sock.recv(1024)
            if not packet: break
            b_result.append(packet)
            try:
                result = pickle.loads(b"".join(b_result))
                break
            except:
                pass

        # result = pickle.loads(b_result)
        return result

class VTK_Panel_Vehicle(wx.Panel):
    def __init__(self, parent):
        """
        initializes the vtk viewer

        Parameters
        ----------
        parent : wx.Panel
            the parent panel
        """
        wx.Panel.__init__(self, parent, style=wx.SIMPLE_BORDER)
        vtk.vtkObject.GlobalWarningDisplayOff()
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.widget = wxVTKRenderWindowInteractor(self, -1)
        self.widget.SetInteractorStyle(self.style)
        self.widget.Enable(1)
        self.widget.AddObserver("ExitEvent", lambda o, e, f=self: f.Close())
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.widget, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.demo_frame = self.GetTopLevelParent()
        self.Layout()
        self.camera = vtk.vtkCamera()
        self.widget.RemoveObservers('CharEvent')
        self.camera.SetPosition(0, -100, 0)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.SetViewUp(0, 0, 1)
        self.camera.SetParallelProjection(True)

        self.ren = vtk.vtkRenderer()
        self.ren.SetActiveCamera(self.camera)

        self.geom_mesh_actors = {}
        self.geom_mesh_sym_actors = {}

    def fitToExtents(self):
        """
        fits viewport to model
        """
        try:
            self.ren.ResetCamera(self.ren.ComputeVisiblePropBounds())
        except:
            pass
        self.widget.Render()
        self.renderVTKScreen()
    def updateDrawData(self,):
        pass
    def redraw(self):
        """
        redraws model
        """
        self.updateDrawData()  # Update draw data dictionary
        self.renderVTKScreen()  # Redraw VTK Panel
    def renderVTKScreen(self):
        """
        renders model
        """
        self.widget.GetRenderWindow().AddRenderer(self.ren)
        self.ren.RemoveAllViewProps()  # Clears VTK Panel before redrawing contents
        for geom, actor in self.geom_mesh_actors.items():
            self.ren.AddActor(actor)
            for sym in self.geom_mesh_sym_actors[geom]:
                self.ren.AddActor(sym)
        self.ren.SetBackground([255, 255, 255])
    def _quad_tess(self, xyz_grid):
        """
        returns a vtk actor that draws the xyz grid as a quad tess

        Parameters
        ----------
        xyz_grid : list
            a 2d list of points

        Returns
        -------
        vtk.Actor
            The vtk actor
        """
        vtk_points = vtk.vtkPoints()
        vtk_points.SetData(npsup.numpy_to_vtk(xyz_grid.reshape(-1,3),))
        cell = vtk.vtkCellArray()
        row_length = len(xyz_grid[0,:,0])
        col_length = len(xyz_grid[:,0,0])
        for i in range(0,row_length-1):
            for j in range(0,col_length-1):
                quad = vtk.vtkQuad()
                quad.GetPointIds().SetId(0, (i+0)*col_length+(j+0))
                quad.GetPointIds().SetId(1, (i+1)*col_length+(j+0))
                quad.GetPointIds().SetId(2, (i+1)*col_length+(j+1))
                quad.GetPointIds().SetId(3, (i+0)*col_length+(j+1))
                cell.InsertNextCell(quad)
        mesh_1 = vtk.vtkPolyData()
        mesh_1.SetPoints(vtk_points)
        mesh_1.SetPolys(cell)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(mesh_1)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetRepresentationToWireframe()

        actor.GetProperty().SetEdgeVisibility(True)
        actor.GetProperty().SetColor([0, 0, 255])

        return actor

    def make_geom_tesselations(self, tess_dict):
        """
        creates an actor for all opensp components

        Parameters
        ----------
        tess_dict : dict
            a dict containing points for each component
        """
        self.geom_mesh_actors = {}
        self.geom_mesh_sym_actors = {}
        for name, tess in tess_dict.items():
            info = tess[0]
            syms = tess[1]
            actor = self._quad_tess(info)
            actor.GetProperty().SetRepresentationToWireframe()
            self.geom_mesh_actors[name] = actor

            self.geom_mesh_sym_actors[name] = []
            for sym in syms:
                if len(sym)>0:
                    actor = self._quad_tess(sym)
                    actor.GetProperty().SetRepresentationToWireframe()

                    self.geom_mesh_sym_actors[name].append(actor)

class DemoApp(wx.App):
    def OnInit(self):
        self.m_frame = DemoFrame(make_vtk=True)
        self.m_frame.Show()
        return True

def start_app(make_vtk=False):
    app = DemoApp(0)
    app.MainLoop()

if __name__ == "__main__":
    start_app(True)