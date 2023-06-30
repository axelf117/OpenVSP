ExternalProject_Add( DELABELLA
	URL ${CMAKE_CURRENT_SOURCE_DIR}/delabella-b1a8f89ac561.zip
	CMAKE_ARGS -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}
		-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
		-DCMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS}
		-DCMAKE_C_FLAGS=${CMAKE_C_FLAGS}
		-DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR>
		-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
)
ExternalProject_Get_Property( DELABELLA INSTALL_DIR )
SET( DELABELLA_INSTALL_DIR ${INSTALL_DIR} )
