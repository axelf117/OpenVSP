CMAKE_MINIMUM_REQUIRED(VERSION 3.24)

IF( NOT VSP_NO_GRAPHICS )

  # ADD_FLTK_FILE is a function that roughly replaces FLTK_WRAP_UI.
  # ADD_FLTK_FILE only works one file at a time -- and it is passed the base file name (without extension).
  # Also, ADD_FLTK_FILE passes causes fltk to generate source files with the .C and .H extension instead of
  # .cxx and .h.
  function( ADD_FLTK_FILE prjname basename)
    add_custom_command(
      OUTPUT ${basename}.C ${basename}.H
      MAIN_DEPENDENCY ${basename}.fl
      COMMAND fltk::fluid -o .C -h .H -c ${CMAKE_CURRENT_SOURCE_DIR}/${basename}.fl
    )
    set( ${prjname}_FLTK_UI_SRCS
      ${${prjname}_FLTK_UI_SRCS} ${basename}.C
      PARENT_SCOPE
    )
  endfunction()

  ADD_FLTK_FILE( viewerscreens ContourLevel )
  ADD_FLTK_FILE( viewerscreens CuttingPlane )
  ADD_FLTK_FILE( viewerscreens viewerUI )
  # These three lines are roughly equivalent to:
  #  FLTK_WRAP_UI( viewerscreens
  #  ContourLevel.fl
  #  CuttingPlane.fl
  #  viewerUI.fl
  #  )

  INCLUDE_DIRECTORIES(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
    ${STB_INCLUDE_DIR}
    ${FLTK_INCLUDE_DIR}
  )

  ADD_LIBRARY(viewerscreens ${viewerscreens_FLTK_UI_SRCS} )

  if( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    TARGET_COMPILE_OPTIONS( viewerscreens PUBLIC -Wno-deprecated-declarations)
  endif()

  IF( "${CMAKE_SYSTEM}" MATCHES "Linux")
    SET( LINUX_LIBS
      pthread
    )
  ELSE()
    SET( LINUX_LIBS )
  ENDIF()

  ADD_EXECUTABLE(vspviewer
    EngineFace.C
    RotorDisk.C
    VSP_Agglom.C
    VSP_Body.C
    VSP_DegenGeom.C
    VSP_Edge.C
    VSP_Grid.C
    VSP_Node.C
    VSP_Tris.C
    VSP_Wing.C
    binaryio.C
    FEM_Node.C
    Optimization_Node.C
    glf.C
    glviewer.C
    quat.C
    trackball.C
    utils.C
    vspaero_viewer.C
    CharSizes.H
    ControlSurface.H
    EngineFace.H
    GL_VIEWER.forward.declaration.H
    PropElement.H
    RotorDisk.H
    VSP_Agglom.H
    VSP_Body.H
    VSP_DegenGeom.H
    VSP_Edge.H
    VSP_Grid.H
    VSP_Node.H
    VSP_Tris.H
    VSP_Wing.H
    binaryio.H
    FEM_Node.H
    Optimization_Node.H
    glf.H
    glviewer.H
    quat.H
    surfIDs.H
    trackball.H
    utils.H
  )

  TARGET_COMPILE_DEFINITIONS( vspviewer PRIVATE -DDO_GRAPHICS -DOCTREE_DO_GRAPHICS )

  if( CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    TARGET_COMPILE_OPTIONS( vspviewer PUBLIC -Wno-deprecated-declarations)
  endif()

  TARGET_LINK_LIBRARIES(vspviewer
    viewerscreens
    stb_image
    ${FLTK_LIBRARIES}    # Should be: fltk::gl    this way for legacy Ubuntu
    ${LINUX_LIBS}
    ${OPENGL_LIBRARIES}
  )

  INSTALL( TARGETS vspviewer RUNTIME DESTINATION . )

  IF( SWIG_FOUND AND PYTHONLIBS_FOUND )
    INSTALL( TARGETS vspviewer RUNTIME DESTINATION python/openvsp/openvsp )

    add_custom_command(TARGET vspviewer POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy
            $<TARGET_FILE:vspviewer>
            ${CMAKE_BINARY_DIR}/python_pseudo/openvsp/openvsp/$<TARGET_FILE_NAME:vspviewer> )
  ENDIF( SWIG_FOUND AND PYTHONLIBS_FOUND )

  get_property( is_multi_config GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG )

  if ( is_multi_config )
          SET( conf_suffix "$<CONFIG>/" )
  endif()

  add_custom_command(TARGET vspviewer POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy
          $<TARGET_FILE:vspviewer>
          ${CMAKE_BINARY_DIR}/src/vsp/${conf_suffix}$<TARGET_FILE_NAME:vspviewer> )

ENDIF()
