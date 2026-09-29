import React, { useEffect, useState } from "react";
import { View, TextInput, TouchableOpacity, Text, Platform } from "react-native";
import { WebView } from "react-native-webview";
import { UploadFile } from "../widgets/uploadFile";
import { getSessionData } from "../services/storage";
import { httpRequest } from "../services/generalService";
import { ExecutionAnalysisRunning } from "../widgets/executionAnalysisRunning";

const NetSuiteLoginForm: React.FC<{ setMenuStatus:(value:boolean)=>void, isReportActive:boolean, setIsReportActive:(value:boolean) => void, session:(value:boolean)=>void }> = ({ setMenuStatus, isReportActive, setIsReportActive, session }) => {
  /*const [id, setId] = useState("");
  const [showWebView, setShowWebView] = useState(false);

  const url = `https://${id}-sb1.app.netsuite.com/app/login/secure/enterpriselogin.nl?c=${id}_SB1&redirect=%2Fapp%2Fcenter%2Fcard.nl%3Fsc%3D-29%26whence%3D&whence=`;

  const handleSubmit = () => {
    if (id.trim() !== "") {
      setShowWebView(true);
    }
  };

  return (
    <View className="flex items-center justify-center bg-gray-100  h-screen">
      {!showWebView ? (
        // 📌 Pantalla de ingreso de ID
        <View className="bg-white p-8 rounded-xl shadow-lg w-96">
          <Text className="text-lg font-semibold text-center mb-4">Enter Your NetSuite ID</Text>
          <TextInput
            className="p-3 border border-gray-300 rounded-lg mb-4 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
            placeholder="Enter NetSuite ID"
            placeholderTextColor="#9CA3AF"
            value={id}
            onChangeText={setId}
          />
          <TouchableOpacity
            className="bg-blue-600 py-3 px-6 rounded-lg shadow-sm hover:bg-blue-700 active:bg-blue-800 transition-colors"
            onPress={handleSubmit}
            disabled={!id.trim()}
          >
            <Text className="text-white text-center font-semibold">Submit</Text>
          </TouchableOpacity>
        </View>
      ) : (
        // 📌 Pantalla con WebView después de ingresar el ID
        <View className="flex-1 w-full">
          {Platform.OS === "web" ? (
            <iframe
              src={url}
              className="w-full h-screen border-none"
              title="NetSuite Login"
            />
          ) : (
            <WebView source={{ uri: url }} style={{ flex: 1 }} />
          )}
        </View>
      )}
    </View>
  );*/

  const [refreshKey, setRefreshKey] = useState(0);
  const [analysisIsCompleted, setAnalysisIsCompleted] = useState(true)

  const refresh = () => {
    setRefreshKey((refreshKey) => refreshKey + 1);
  };

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
        {isReportActive || !analysisIsCompleted
        ?
          <View className="flex-1 p-6 space-y-8 justify-center items-center w-full overflow-auto">
            <View className='bg-white p-6 rounded-lg shadow-lg w-full max-w-xl min-w-[260px] mx-auto'>
              <Text className='font-semibold text-lg mb-4'>
                Please upload a ZIP file containing the following:
              </Text>
              <View className='list-inside'>
                <Text className='text-base mb-2'>roles.csv or roles.xlsx</Text>
                <Text className='text-base mb-2'>employees.csv or employees.xlsx</Text>
                <Text className='text-base mb-2'>subsidiaries.csv or subsidiaries.xlsx</Text>
                <Text className='text-base mb-2'>employee_global_permissions.csv or employee_global_permissions.xlsx</Text>
                <Text className='text-base mb-2'>employee_roles.csv or employee_roles.xlsx</Text>
                <Text className='text-base mb-2'>role_subsidiaries.csv or role_subsidiaries.xlsx</Text>
                <Text className='text-base mb-2'>role_permissions.csv or role_permissions.xlsx</Text>
              </View>
              <UploadFile endpoint='/upload_zip' refresh={refresh} setMenuStatus={setMenuStatus} setAnalysisIsCompleted={setAnalysisIsCompleted} setIsReportActive={setIsReportActive} session={session}/>
            </View>
          </View>
        :
          <ExecutionAnalysisRunning />
        }
      </View>
  )
};

export default NetSuiteLoginForm;
