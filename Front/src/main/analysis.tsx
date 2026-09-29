import React, { useEffect, useState } from 'react';
import { View, Text, Pressable, Platform } from 'react-native';
import { FilterTable } from '../widgets/filterTable';
import { getSessionData } from '../services/storage';
import { httpRequest } from '../services/generalService';
import { ExecutionAnalysisRunning } from '../widgets/executionAnalysisRunning';


const AnalysisComponent: React.FC<{ isReportActive:boolean, session:(value:boolean)=>void }> = ({ isReportActive, session }) => {
  const [refreshKey2, setRefreshKey2] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const [analysisIsCompleted, setAnalysisIsCompleted] = useState(true)
  
  const refresh2 = () =>{
    setRefreshKey2((refreshKey2) => refreshKey2 + 1)
  }

  const buttons = [
    { label: "Individual Role Risk Detailed", path: "/individual_role_risk_detailed"},
    { label: "Individual Role Risk", path: "/individual_role_risk"},
    { label: "User Risk Detailed", path: "/user_risk_detailed"},
    { label: "User Risk", path: "/user_risk"},
  ];
  
  const [endpoint, setEndpoint] = useState(buttons[0].path)

  const changeDashboard = async(endpoint:any, actual_endpoint:any) => {
    //console.log(endpoint)
    //console.log(actual_endpoint)
    if (endpoint != actual_endpoint) {
      setEndpoint(endpoint)
      refresh2()
    }
  }

  useEffect(()=>{
    const getAnalysisStatus = async () => {
      const sessionData = getSessionData();
      if (sessionData && sessionData.Company){
        const analysisStatus = await httpRequest('POST', '/is_analysis_process_running', sessionData)
        if (analysisStatus.detail){
          if (Platform.OS == 'web'){
            window.alert(analysisStatus.detail)
          }
        }else{
          //console.log(analysisStatus)
          setAnalysisIsCompleted(analysisStatus)
        }
      }else{
        session(false)
      }
    }
    getAnalysisStatus();
  }, [])

  return (
    <View className="flex flex-col h-screen min-h-screen bg-gray-100 font-sans w-full overflow-hidden">
      {/* Header */}
      <View className="flex items-center justify-center h-[110px] bg-gradient-to-r from-[#0d1b2a] via-[#13263c] to-[#0b1724] border-b border-white/10 shadow-[0_20px_60px_rgba(4,20,32,0.45)]">
        <Text className="text-center text-white tracking-[0.12em] font-extrabold text-5xl uppercase">Analysis</Text>
      </View>

      {
        isReportActive || !analysisIsCompleted
        ?
          /* Main Content */
          <View className="flex flex-1 flex-col p-4 space-y-8 min-h-0 overflow-hidden w-full">
            {/* Users Section */}
            <View className="flex flex-1 flex-col bg-white border border-gray-200 rounded-lg shadow-lg min-h-0 w-full overflow-hidden">
              <View className="flex flex-col min-h-full max-h-full w-full">
                <View className="p-4 flex flex-col sm:flex-row flex-wrap gap-4 justify-center items-center bg-slate-500 rounded-t-lg items-stretch w-full">
                  {buttons.map(({ label, path }) => (
                    <Pressable
                      key={path}
                      className="flex inline-flex flex-auto min-w-[160px] px-4 py-3 bg-gradient-to-r from-blue-400 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 justify-center items-center text-center"
                      onPress={async () => await changeDashboard(path, endpoint)}
                      android_ripple={{ color: "#2563eb" }}
                    >
                      <Text className="text-white text-sm">{label}</Text>
                    </Pressable>
                  ))}
                </View>
                <View key={`${refreshKey}-${refreshKey2}-table2`} className="flex-1 p-2 min-h-0 w-full rounded overflow-hidden overflow-auto">
                  <FilterTable endpoint={endpoint} session={session}></FilterTable>
                </View>
              </View>
            </View>
          </View>
        :
          <ExecutionAnalysisRunning />
      }
    </View>
  );
};  

export default AnalysisComponent;