import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, Platform, Pressable} from 'react-native';
import { download, httpRequest, url } from '../services/generalService';
import { getSessionData } from '../services/storage';
import WebView from "react-native-webview";


const AnalysisComponent = () => {
  const [refreshKey2, setRefreshKey2] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  const refresh2 = () =>{
    setRefreshKey2((refreshKey2) => refreshKey2 + 1)
  }

  const [loading, setLoading] = useState(true);
  const [text, setText] = useState('');
  const [html, setHtml] = useState('');
  const [dash, setDash] = useState('');
  const endpoint = '/filter_table'
  /*let isPermissionsLoaded = false;
  let isUsersLoaded = false;*/
  let isDetailed = false;
  let isSimplified = false;
  let isClientData = false;
  let isClientDataSimplified = false;

  const [isDisabled, setIsDisabled] = useState(false)

  useEffect(()=>{
    const firstLoad = async() => {
      const sessionData = await getSessionData();
      if (sessionData && sessionData.Company){
        const newSessionData = {
          ...sessionData,
          Option: 0
        }
        await getFiltered(newSessionData);
      }
    }
    firstLoad();
  }, [])

  const getFiltered = async(newSessionData:any) => {
    setLoading(true);
    const response = await httpRequest('POST', endpoint, newSessionData);
    if (response){
      if (typeof response === 'string'){
        setHtml(response)
      }else{
        if (response.url_complementation){
          setDash(`${url}${response.url_complementation}`)
          if (newSessionData.Option == '0' || newSessionData.Option == 0){
            isDetailed = true;
          }else{
            if (newSessionData.Option == '1' || newSessionData.Option == 1){
              isSimplified = true;
            }else{
              if (newSessionData.Option == '2' || newSessionData.Option == 2){
                isSimplified = true;
              }else{
                isClientDataSimplified = true;
              }
            }
          }
        }else{
          setText(response.detail??'Loading Error')
        }
      }
    }else{
      setText('Loading Error')
    }
    setLoading(false);
  }

  const changeDashboard = async(option:any) => {
    const sessionData = await getSessionData();
    if (sessionData && sessionData.Company){
      setLoading(true);
      switch (option){
        case 0:
          if (isDetailed){
            setDash(`${url}/get_Role_Level_Conflicts_Filtered_${sessionData.UserID}/`)
          }else{
            const newSessionData = {
              ...sessionData,
              Option: 0
            }
            await getFiltered(newSessionData);
          }
          break;
        case 1:
          if (isSimplified){
            setDash(`${url}/get_Role_Level_Conflicts_Simplified_Filtered_${sessionData.Company}/`)
          }else{
            const sessionData = await getSessionData();
            if (sessionData && sessionData.Company){
              const newSessionData = {
                ...sessionData,
                Option: 1
              }
              await getFiltered(newSessionData);
            }
          }
          break;
        case 2:
          if (isClientData){
            setDash(`${url}/get_Merged_Users_to_Permissions_Filtered_${sessionData.Company}/`)
          }else{
            const sessionData = await getSessionData();
            if (sessionData && sessionData.Company){
              const newSessionData = {
                ...sessionData,
                Option: 2
              }
              await getFiltered(newSessionData);
            }
          }
          break;
        default:
          if (isClientDataSimplified){
            setDash(`${url}/get_Single_Role_Conflicts_Filtered_${sessionData.Company}/`)
          }else{
            const sessionData = await getSessionData();
            if (sessionData && sessionData.Company){
              const newSessionData = {
                ...sessionData,
                Option: 3
              }
              await getFiltered(newSessionData);
            }
          }
      }
      setLoading(false);
    }
  }


const buttons = [
  { label: "Role Level Detailed", index: 0 },
  { label: "Role Level Simplified", index: 1 },
  { label: "Client Data", index: 2 },
  { label: "Client Data Simplified", index: 3 },
];

  return (
    <View className="flex flex-col min-h-screen bg-gray-100 font-sans w-full">
    {/* Header */}
    <View className="flex items-center justify-center h-[100px] bg-[#4c2b31] text-white text-2xl font-bold shadow-lg">
    <Text className="text-center text-white tracking-wide  font-bold  text-4xl">Analysis</Text>
    </View>


    {/* Main Content */}
    <View className="flex p-3 space-y-8">
      {/* Users Section */}
      <View className="bg-white border border-gray-200 rounded-lg shadow-lg">
      <View className="p-4 flex flex-row justify-center items-center space-x-4 bg-slate-500 rounded-t-lg">
      {buttons.map(({ label, index }) => (
        <Pressable
          key={index}
          className="inline-flex px-8 py-4 bg-gradient-to-r from-blue-400 to-blue-500 hover:from-blue-500 hover:to-blue-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          onPress={async () => await changeDashboard(index)}
          android_ripple={{ color: "#2563eb" }}
        >
          <Text className="text-white text-sm">{label}</Text>
        </Pressable>
      ))}
    </View>

        <View className="p-6">
          <View key={`${refreshKey}-${refreshKey2}-table2`} className="h-[500px] w-full  rounded overflow-hidden">
            <ScrollView className="w-full" contentContainerStyle={{ flexGrow: 1 }}>
              {
                loading?
                  <ActivityIndicator size="large" />
                :text!=''?
                  <Text className="text-center text-gray-500">{text}</Text>
                :Platform.OS=='web'?(
                  dash!=''?
                    <iframe src={dash}  allowFullScreen style={{height: '100%'}}/>
                  :
                    <iframe srcDoc={html} allowFullScreen style={{height: '100%'}}/>
                )
                :
                  <WebView
                    source={{ html: html }}
                  />
              }
            </ScrollView>
            {/*<View className="p-3 flex flex-row justify-center items-center space-x-6  ">
              <TouchableOpacity className="px-8 py-4 bg-blue-400 w-36 items-center font-semibold rounded-xl shadow-lg hover:bg-blue-600 active:bg-blue-700 transition-colors duration-200" onPress={async()=>await download(isDisabled, setIsDisabled, '/get_results_filtered')}>
                {
                  !isDisabled
                  ?
                  <Text className="text-white text-lg font-medium">Download</Text>
                  :
                  <ActivityIndicator size="small" color="#ffffff"/>
                }
              </TouchableOpacity>
            </View>*/}
          </View>
        </View>
      </View>
    </View>
  </View>
  );
};  

export default AnalysisComponent;