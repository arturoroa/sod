import React, { useRef, useState } from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { RenderWebView } from '../widgets/webviews';
import { Body, Header } from '../widgets/components';
import { FilterTable } from '../widgets/filterTable';

const SOD:React.FC<{session:(value:boolean)=>void}> = ({session}) => {

  //const [refreshKey, setRefreshKey] = useState(0);

  //const refresh = () => {
  //  setRefreshKey((refreshKey) => refreshKey + 1)
  //};

  const title = 'SOD RuleSet'
  const endpoints = ['/SOD_RuleSet', '/personal_SOD_RuleSet']
  const ref = useRef<any>(null);

  const createSODRule = async () => {
    if (ref.current) {
        await ref.current.createSODRule()
    }
  }

  const removeSelectedSODRules = async () => {
    if (ref.current) {
        await ref.current.removeSelectedSODRules()
    }
  }

  const resetSODRules = async () => {
    if (ref.current) {
        await ref.current.resetSODRules()
    }
  }

  const buttons = [
    { label: "Add SOD Rule", color: "bg-green-500", action: createSODRule},
    { label: "Remove Selected SOD Rules", color: "bg-blue-500", action: removeSelectedSODRules},
    { label: "Reset SOD Rules",  color: "bg-red-500", action: resetSODRules}
  ];

  return (
    //<View className="flex flex-col min-h-screen bg-gray-100 font-sans w-full h-auto">
    //  {/* Header */}
    //  <View className="flex items-center justify-center h-[100px] bg-[#4c2b31] text-white text-2xl font-bold shadow-lg">
    //    <Text className="text-center text-white tracking-wide  font-bold  text-4xl">SOD Rule Set</Text>
    //  </View>
    //  <RenderWebView key={refreshKey} endpoint='/get_SOD_html' option={true} />
    //  {/*<View className="flex-1 p-6 space-y-8">
    //    {/* <UploadFile endpoint='/upload_SOD' refresh={refresh}/> */}
    //    {/*<View className="bg-white border border-gray-200 rounded-lg shadow-lg">
    //      <Text className="text-xl font-semibold bg-slate-500 text-white py-4 rounded-t-lg text-center">
    //        SOD Rule Set
    //      </Text>
    //      <View className="p-6">
    //        <View className="h-[500px] w-full  rounded overflow-hidden">
    //          {/* /get_SOD_html 
    //          <Text  className="text-center text-gray-500">[Users Table Placeholder]</Text>
    //          <ScrollView className="w-full" contentContainerStyle={{ flexGrow: 1 }}>
    //            <RenderWebView key={refreshKey} endpoint='/get_SOD_html' option={false} />
    //          </ScrollView>              
    //        </View>
    //      </View>
    //    </View>*/}
    //  {/*</View>*/}
    //</View>
    
    <View className="flex flex-col h-screen min-h-screen bg-gray-100 font-sans min-w-[320px] w-full overflow-hidden">
        <Header title={title}></Header>
        <View className='flex flex-col flex-1 min-h-0 p-4 space-y-6 overflow-hidden'>
            <View className='flex-1 min-h-0 w-full overflow-hidden'>
                <Body endpoint={endpoints[0]} session={session} fullHeight={false} />
            </View>
            <View className='flex-1 min-h-0 w-full overflow-hidden'>
                <View className="flex flex-1 flex-col p-4 space-y-8 min-h-0 w-full overflow-hidden h-full">
                    <View className="flex flex-col bg-white border border-gray-200 rounded-lg shadow-lg min-h-0 w-full overflow-hidden h-full">
                        <View className="flex flex-col min-h-full h-full w-full">
                            <View className="p-4 flex flex-col sm:flex-row flex-wrap gap-4 justify-center items-center bg-slate-500 rounded-t-lg items-stretch w-full">
                                {buttons.map(({ label, color, action }) => (
                                    <Pressable
                                        key={label}
                                        className={`flex inline-flex flex-auto min-w-[160px] px-8 py-4 text-white ${color} font-semibold rounded-lg shadow-lg hover:shadow-xl transform transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 justify-center items-center`}
                                        onPress={async () => await action()}
                                    >
                                        <Text className="text-white text-sm">{label}</Text>
                                    </Pressable>
                                ))}
                            </View>
                            <View className="flex-1 min-h-0 overflow-hidden rounded">
                                <View className="flex-1 min-h-0 overflow-hidden">
                                    <FilterTable endpoint={endpoints[1]} ref={ref} specialFeatures={true} session={session}></FilterTable>
                                </View>
                            </View>
                        </View>
                    </View>
                </View>
            </View>
        </View>
    </View>
  );
};

export default SOD;