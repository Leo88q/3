# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 3.20)
project(NoriwakeMac LANGUAGES C CXX)
if(NOT APPLE)
  message(FATAL_ERROR "This is the explicit macOS desktop profile, not Android/Linux")
endif()
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
get_filename_component(ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
set(GAME "${ROOT}/native/zooshi")
set(DEPS "${GAME}/dependencies")
set(GENERATED "${CMAKE_BINARY_DIR}/generated")
find_package(PkgConfig REQUIRED)
# Deliberate macOS-only system dependencies, recorded by the driver. Android pins
# are NOT replaced. Modern SDL2 is needed for Apple Silicon/Cocoa.
pkg_check_modules(MACLIBS REQUIRED IMPORTED_TARGET sdl2>=2.0 SDL2_mixer>=2.0
  freetype2 harfbuzz libunibreak gumbo libwebp)
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/sources.json" SOURCE_MANIFEST)
string(JSON GROUP_COUNT LENGTH "${SOURCE_MANIFEST}" sources)
math(EXPR GROUP_LAST "${GROUP_COUNT}-1")
set(CORE_SOURCES)
foreach(INDEX RANGE ${GROUP_LAST})
  string(JSON GROUP MEMBER "${SOURCE_MANIFEST}" sources ${INDEX})
  string(JSON COUNT LENGTH "${SOURCE_MANIFEST}" sources ${GROUP})
  math(EXPR LAST "${COUNT}-1")
  foreach(I RANGE ${LAST})
    string(JSON SOURCE GET "${SOURCE_MANIFEST}" sources ${GROUP} ${I})
    if(GROUP STREQUAL "game")
      list(APPEND CORE_SOURCES "${GAME}/${SOURCE}")
    else()
      list(APPEND CORE_SOURCES "${DEPS}/${GROUP}/${SOURCE}")
    endif()
  endforeach()
endforeach()
add_executable(noriwake main.cpp ${CORE_SOURCES})
set_target_properties(noriwake PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
target_compile_definitions(noriwake PRIVATE FPLBASE_OPENGL FPLBASE_ANDROID_VR=0
  FLATUI_HAS_GUMBO DEBUG=1
  BREADBOARD_MODULE_LIBRARY_BUILD_MATHFU
  BREADBOARD_MODULE_LIBRARY_BUILD_CORGI_COMPONENT_LIBRARY
  BREADBOARD_MODULE_LIBRARY_BUILD_PINDROP)
# Only the original FPLBase texture implementation owns STB definitions.
set_source_files_properties("${DEPS}/fplbase/src/texture_common.cpp" PROPERTIES
  COMPILE_DEFINITIONS "STB_IMAGE_IMPLEMENTATION;STB_IMAGE_RESIZE_IMPLEMENTATION")
target_include_directories(noriwake PRIVATE "${GENERATED}" "${GAME}/src"
  "${DEPS}/fplutil/libfplutil/include"
  "${DEPS}/bulletphysics/src" "${DEPS}/stb"
  "${DEPS}/flatui/include/flatui" "${DEPS}/flatui/src" "${DEPS}/flatui/src/libpng_to_stbimage"
  "${DEPS}/fplbase/src" "${DEPS}/motive/src"
  "${DEPS}/pindrop/src" "${DEPS}/pindrop/src/mixer/sdl_mixer" "${DEPS}/pindrop/src/asynchronous_loader"
  "${DEPS}/corgi/component_library/include" "${DEPS}/breadboard/module_library/include")
foreach(DEP flatbuffers mathfu vectorial fplbase motive pindrop corgi breadboard flatui scene_lab)
  target_include_directories(noriwake PRIVATE "${DEPS}/${DEP}/include")
endforeach()
target_link_libraries(noriwake PRIVATE PkgConfig::MACLIBS
  "-framework OpenGL" "-framework CoreFoundation" "-framework CoreGraphics" "-framework CoreText")
