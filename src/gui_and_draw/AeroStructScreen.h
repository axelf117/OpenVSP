//
// This file is released under the terms of the NASA Open Source Agreement (NOSA)
// version 1.3 as detailed in the LICENSE file which accompanies this software.
//

// Manage coupled aero / structural analyses
// Rob McDonald
//
//////////////////////////////////////////////////////////////////////

#if !defined(VSPAEROSTRUCTSCREEN__INCLUDED_)
#define VSPAEROSTRUCTSCREEN__INCLUDED_

#include "ScreenBase.h"
#include "GuiDevice.h"

#include <FL/Fl.H>
#include <FL/Fl_Text_Buffer.H>

using std::string;
using std::vector;

class AeroStructScreen : public BasicScreen
{
public:
    AeroStructScreen( ScreenMgr* mgr );
    virtual ~AeroStructScreen();
    void Show();
    void Hide();
    bool Update();

    void CallBack( Fl_Widget *w );
    static void staticScreenCB( Fl_Widget *w, void* data )
    {
        ( static_cast <AeroStructScreen*> ( data ) )->CallBack( w );
    }

    void GuiDeviceCallBack( GuiDevice* gui_device );

protected:

    GroupLayout m_GlobalLayout;

    TriggerButton m_ShowVSPAEROGUI;
    TriggerButton m_ExecuteVSPAERO;


};


#endif