ExternalProject_Add( CODEELI
	URL ${CMAKE_SOURCE_DIR}/Code-Eli-638f8af36afa.zip
	CMAKE_ARGS -DCMAKE_INSTALL_PREFIX:PATH=<INSTALL_DIR>
		-DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}
		-DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
		-DCMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS}
		-DCMAKE_C_FLAGS=${CMAKE_C_FLAGS}
		-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
	BUILD_COMMAND ""
	INSTALL_COMMAND ""
)
ExternalProject_Get_Property( CODEELI BINARY_DIR SOURCE_DIR )
SET( CODEELI_INSTALL_DIR ${BINARY_DIR} ${SOURCE_DIR})