import React, { useEffect, useState } from 'react';
import { View, Text, Platform, ScrollView } from 'react-native';
import { Charts } from '../widgets/charts';
import { Cards } from '../widgets/cards';
import { SimpleTable } from '../widgets/simpleTable';
import { Header } from '../widgets/components';
import { getSessionData } from '../services/storage';
import { httpRequest } from '../services/generalService';
import { ExecutionAnalysisRunning } from '../widgets/executionAnalysisRunning';

const TailwindAdaptedComponent: React.FC<{ isReportActive:boolean, session:(value:boolean)=>void}> = ({ isReportActive, session }) => {

  const [refreshKey, setRefreshKey] = useState(0)
  const [refreshKey2, setRefreshKey2] = useState(0)
  const [analysisIsCompleted, setAnalysisIsCompleted] = useState(true)

  const refresh = () =>{
    setRefreshKey((refreshKey) => refreshKey + 1)
  }

  const refresh2 = () =>{
    setRefreshKey2((refreshKey2) => refreshKey2 + 1)
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
          setAnalysisIsCompleted(analysisStatus)
        }
      }else{
        session(false)
      }
    }
    getAnalysisStatus();
  }, [])

  return (
    <View className="flex flex-col h-screen bg-gray-100 font-sans w-full overflow-hidden">
      <Header title="Dashboard" />
      {
        isReportActive || !analysisIsCompleted
        ?
          <ScrollView className='flex-1 h-full' contentContainerStyle={{ minHeight: '100%' }}>
            <SimpleTable endpoint='/user_risk_by_company' session={session}></SimpleTable>
            <View className="flex flex-row flex-wrap w-full justify-center">
              <Charts endpoint='/top_user_risks' type='bar' session={session}></Charts>
              <Charts endpoint='/top_10_role_risk' type='bar' session={session}></Charts>
              <Charts endpoint='/high_risk_business_process' type='bar' session={session}></Charts>
              <Charts endpoint='/top_10_user_risk' type='bar' session={session}></Charts>
              <Charts endpoint='/risk_level' type='doughnut' session={session}></Charts>
            </View>
            <View className="flex flex-row flex-wrap w-full justify-center">
              <Cards endpoint='/users_with_risk' type='percentage' session={session}></Cards>
              <Cards endpoint='/roles_with_risk' type='percentage' session={session}></Cards>
              <Cards endpoint='/users_with_globals' type='percentage' session={session}></Cards>
              <Cards endpoint='/system_data' type='normal' session={session}></Cards>
              <Cards endpoint='/analysis_summary' type='normal' session={session}></Cards>
            </View>
          </ScrollView>
        :
          <ExecutionAnalysisRunning />
      }
      {/*<RenderWebView endpoint='/dashboard' option={true}/>*/}
      {/* Main Content */}
      {/*<View className="flex-1 p-6 space-y-8">
        {/* Update Resources Section */}
        {/*<View className="bg-white border border-gray-200 rounded-lg shadow-lg flex">
          <Text className="text-xl font-semibold bg-slate-500 text-white py-4 rounded-t-lg text-center">
          Dashboard
          </Text>
          <View className="p-6">
            <View key={`${refreshKey}-${refreshKey2}-table3`} className="h-[500px] w-full  rounded overflow-hidden">
              <RenderWebView endpoint='/dashboard' option={true}/>
            </View>
          </View>
        </View>*/}
      {/*</View>*/}
    </View>
  );
};

export default TailwindAdaptedComponent;
