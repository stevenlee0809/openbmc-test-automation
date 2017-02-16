*** Settings ***
Documentation     This testsuite is for testing inventory
Suite Teardown    Delete All Sessions
Resource          ../lib/rest_client.robot
Resource          ../lib/utils.robot
Resource          ../lib/state_manager.robot
Resource          ../lib/openbmc_ffdc.robot
Library           ../lib/utilities.py
Library           String
Library           Collections

Variables         ../data/variables.py

Suite setup       Setup The Suite
Test Teardown     FFDC On Test Case Fail

Force Tags  chassisboot  inventory

*** Test Cases ***

Minimal CPU Inventory
    [Tags]  Minimal_CPU_Inventory

    ${count}=  Get Total Present  cpu
    Should Be True  ${count}>${0}

Minimal DIMM Inventory
    [Tags]  Minimal DIMM Inventory

    ${count}=  Get Total Present  dimm
    Should Be True  ${count}>=${2}

Minimal Core Inventory
    [Tags]  Minimal_Core_Inventory

    ${count}=  Get Total Present  core
    Should Be True  ${count}>${0}

Minimal Memory Buffer Inventory
    [Tags]  Minimal_Memory_Buffer_Inventory

    ${count}=  Get Total Present  membuf
    Should Be True  ${count}>${0}

Minimal Fan Inventory
    [Tags]  Minimal_Fan_Inventory

    ${count}=  Get Total Present  fan
    Should Be True  ${count}>${2}

Minimal Main Planar Inventory
    [Tags]  Minimal_Main_Planar_Inventory

    ${count}=  Get Total Present  motherboard
    Should Be True  ${count}>${0}

Minimal System Inventory
    [Tags]  Minimal_System_Inventory

    ${count}=  Get Total Present  system
    Should Be True  ${count}>${0}

Verify CPU VPD Properties
    [Tags]  Verify_CPU_VPD_Properties

    Verify Properties  CPU

Verify DIMM VPD Properties
    [Tags]  Verify_DIMM_VPD_Properties

    Verify Properties  DIMM

Verify Memory Buffer VPD Properties
    [Tags]  Verify_Memory_Buffer_VPD_Properties

    Verify Properties  MEMORY_BUFFER

Verify Fan VPD Properties
    [Tags]  Verify_Fan_VPD_Properties

    Verify Properties  FAN

Verify System VPD Properties
    [Tags]  Verify_System_VPD_Properties

    Verify Properties  SYSTEM


*** Keywords ***

Setup The Suite
    ${host_state}=  Get Host State
    Run Keyword If  '${host_state}' == 'Off'  Initiate Host Boot

    ${resp}=  Read Properties  ${INVENTORY_URI}enumerate
    Set Suite Variable  ${SYSTEM_INFO}  ${resp}
    Log Dictionary  ${resp}

Get Total Present
    [Arguments]  ${type}
    ${l}=  Create List  []
    ${resp}=  Get Dictionary Keys  ${SYSTEM_INFO}
    ${list}=  Get Matches  ${resp}  regexp=^.*[0-9a-z_].${type}[0-9]*$
    : FOR  ${element}  IN  @{list}
    \  Append To List  ${l}  ${SYSTEM_INFO['${element}']['present']}

    ${sum}=  Get Count  ${l}  True
    [Return]  ${sum}

Verify Properties
    [Arguments]  ${type}

    ${list}=  Get VPD Inventory List  ${OPENBMC_MODEL}  ${type}
    : FOR  ${element}  IN  @{list}
    \  ${d}=  Get From Dictionary  ${SYSTEM_INFO}  ${element}
    \  Run Keyword If  ${d['present']} == True  Verify Present Properties  ${d}  ${type}

Verify Present Properties
    [Arguments]  ${d}  ${type}
    ${keys}=  Get Dictionary Keys  ${d}
    Log List  ${keys}
    Log List  ${INVENTORY_ITEMS['${type}']}
    Lists Should Be Equal  ${INVENTORY_ITEMS['${type}']}  ${keys}
