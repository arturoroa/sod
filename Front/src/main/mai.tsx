import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, Image, ScrollView, Platform } from 'react-native';
import TailwindAdaptedComponent from './reports';
import AnalysisComponent from './analysis';
import RoleuserComponent from './roleuser';
import RolepermissionsComponent from './rolepermissions';
import NetSuiteLoginForm from './netsuite';
import SOD from './SOD';
import Ticketing from './ticketing';
import AIAnalysis from './aiAnalysis';
import { clearData, getSessionData } from '../services/storage';
import { download, httpRequest } from '../services/generalService';
import Registro from './registro';
import WebSocketsService from '../services/WebSocketsServices';
import { fromJSON } from 'postcss';
import Employees from './employees';
import Roles from './roles';
import Subsidiaries from './subsidiaries';
import GlobalPermissions from './global_permissions';
import Relationships from './relationships';

type MenuItem = {
  label: string;
  icon: any;
  id: number;
  //component: React.ReactNode;
};

type MenuIndex = {
  id: number;
  component: React.ReactNode;
}

interface NavigationMenuProps {
  setActiveIndex: (index: number) => void;
  session: (value: boolean) => void;
  status: string;
  menuStatus: boolean;
  setMenuStatus:(value:boolean)=>void;
  isReportActive: boolean;
  setIsReportActive: (value: boolean) => void;
}

export const variables = ['company', 'usertype', 'active', 'UserID', 'email', 'phone','/get_user_html_time', '/get_user_html_content', '/get_permission_html_time', '/get_permission_html_content', '/get_user_html_filtered_time', '/get_user_html_filtered_content', '/get_permission_html_filtered_time', '/get_permission_html_filtered_content', 'WebSocketID']

export const logout = async(session: (value: boolean) => void) => {
  const sessionData = await getSessionData();
  if (sessionData && sessionData.Company) {
    const response = await httpRequest('POST', '/logout', sessionData);
    if (response && response.Results == 0) {
      variables.forEach(async variable => {await clearData(variable)})
      WebSocketsService.closeConnection();
      session(false);
    }
  }else{
    session(false)
  }
}



const NavigationMenu: React.FC<NavigationMenuProps> = ({ setActiveIndex, session, status, menuStatus, setMenuStatus, isReportActive, setIsReportActive}) => {
  const [activePage, setActivePage] = useState<string>('Reports'); // Cambiamos a string
  const [isDisabled, setIsDisabled] = useState(false)
  

  const menuItems: MenuItem[] = [
    { label: 'Dashboard', icon: require('../../images/icons/dashboard.png'), id: 1 },
    { label: 'Custom analysis', icon: require('../../images/icons/analysis.png'), id: 2 },
    //{ label: 'Custom analysis', icon: null, id: },
    { label: 'Download Results', icon: require('../../images/icons/descarga.png'), id: 3 },
    // { label: 'Role to Users', icon: require('../../images/icons/roletouser.png'), id: },
    // { label: 'Role to Permissions', icon: require('../../images/icons/rolep.png'), id: },
    { label: 'Roles', icon: require('../../images/icons/roletouser.png'), id: 4 },
    { label: 'Employees', icon: require('../../images/icons/roletouser.png'), id: 5 },
    { label: 'Subsidiaries', icon: require('../../images/icons/roletouser.png'), id: 6 },
    { label: 'Global Permissions', icon: require('../../images/icons/roletouser.png'), id: 7 },
    { label: 'Relationships', icon: require('../../images/icons/roletouser.png'), id: 8 },
    { label: 'SOD RuleSet', icon: require('../../images/icons/sod.png'), id: 9 },
    // { label: 'Workflow Management', icon: require('../../images/icons/worflow.png'), id: },
    // { label: 'Access Provisioning', icon: require('../../images/icons/access_resized.png'), id: },
    // { label: 'Change Log Audit', icon: require('../../images/icons/log.png'), id: },
    // { label: 'Privileged Access Management', icon: require('../../images/icons/pam.png'), id: },
    { label: 'AI Analysis', icon: require('../../images/icons/analysis.png'), id: 11 },
    // { label: 'User Management', icon: require('../../images/icons/user-m.png'), id: },
    // { label: 'Database', icon: null, id: },
    // { label: 'Ticketing', icon: null, id: },
    { label: 'Log out', icon: require('../../images/icons/logout.png'), id: 12 },
  ];
  

  const handleNavigate = async (label: string, index:number) => {
    if (label=='Log out') {
      await logout(session)
    } else {
      if (label=='Download Results'){
        const sessionData = getSessionData()
        if (sessionData && sessionData.Company){
          let executionAnalysisStatus:any = true;
          executionAnalysisStatus = await httpRequest('POST', '/is_analysis_process_running', sessionData)
          if (executionAnalysisStatus || executionAnalysisStatus.detail || !isReportActive){
            let message = 'The risk detection analysis is running, please wait.'
            if (executionAnalysisStatus.detail){
              message = executionAnalysisStatus.detail
            }
            if (Platform.OS == 'web'){
              window.alert(message)
            }
          }else{
            await download(isDisabled, setIsDisabled, '/get_results');
          }
        }else{
          session(false)
        }
      }else{
        setActivePage(label); // Guardamos el label en lugar del componente
        setActiveIndex(index);
      }
    }
  };

  const filteredLabels = ['SOD RuleSet', 'NetSuite Connect', 'AI Analysis', 'Log out']
  const visibleMenuItems = !menuStatus
    ? menuItems.filter((item) => filteredLabels.includes(item.label))
    : menuItems;

  const normalizedStatus = (status || '').toLowerCase();
  const hasWarningStatus = normalizedStatus.includes('running') || normalizedStatus.includes('wait');
  const hasOfflineStatus = normalizedStatus.includes('inactive') || normalizedStatus.includes('disconnected');
  const statusClass = hasOfflineStatus
    ? 'text-[#ffd0da] bg-[#d6455d]/25 border-[#ff8ba0]/35'
    : hasWarningStatus
      ? 'text-[#ffe6c9] bg-[#d08a2e]/25 border-[#ffbf72]/35'
      : 'text-[#cff8ee] bg-[#1c8a77]/25 border-[#82dbc9]/35';

  return (
<View className="w-full lg:min-w-80 lg:w-80 min-h-fit lg:min-h-screen lg:min-h-[100dvh] flex flex-col border-r border-[#7ed2c6]/15 bg-gradient-to-b from-[#0f2027] via-[#163640] to-[#1f4a56] shadow-[0_24px_70px_rgba(4,20,24,0.35)]">
  <View className="px-5 pt-6 pb-4 border-b border-white/10">
    <View className="flex-row items-center gap-3">
      <View className="h-12 w-12 rounded-2xl items-center justify-center border border-[#84e2d2]/35 bg-[#8bf2df]/15 shadow-[0_0_40px_rgba(139,242,223,0.35)]">
        <Text className="text-[#d2fff5] text-lg font-black">S</Text>
      </View>
      <View className="flex-1">
        <Text className="text-[#f1fffb] text-[16px] font-semibold tracking-wide leading-5">Aiver Fianncials</Text>
        <Text className="text-[#f1fffb] text-[16px] font-semibold tracking-wide leading-5">    Risk Detcetor</Text>
      </View>
    </View>
  </View>

  <View className="flex-1 px-4 pt-4">
  <ScrollView
  showsVerticalScrollIndicator={false}
  showsHorizontalScrollIndicator={false}
  >
    {visibleMenuItems.map((item) => (
      <TouchableOpacity
        key={item.label}
        className={`group w-full flex flex-row items-center px-3 py-3 mb-2 rounded-2xl border transition-colors duration-200 ${
          activePage === item.label
            ? 'bg-white/15 border-white/25 shadow-[0_8px_30px_rgba(7,13,21,0.28)]'
            : 'bg-transparent border-transparent hover:bg-white/10 hover:border-white/15'
        }`}
        onPress={() => handleNavigate(item.label, item.id)}
      >
        <View className={`h-9 w-9 rounded-xl items-center justify-center mr-3 ${
          activePage === item.label ? 'bg-[#9bf3e3]/28' : 'bg-white/10'
        }`}>
          <Image
            source={item.icon}
            style={{ width: 18, height: 18 }}
          />
        </View>
        <Text className={`text-[14px] font-semibold ${
          activePage === item.label ? 'text-white' : 'text-[#d6f0eb]'
        }`}>{item.label}</Text>
      </TouchableOpacity>
    ))}
    </ScrollView>
  </View>

  <View className="px-4 pb-3">
    <View className="rounded-2xl border border-white/15 bg-white/10 p-3">
      <View className="flex-row items-center justify-between mb-2">
        <Text className="text-[#bde7df] uppercase tracking-[1.5px] text-[11px] font-bold">Status</Text>
        <View className={`rounded-full border px-2 py-1 ${statusClass}`}>
          <Text className="text-[10px] font-bold">Live</Text>
        </View>
      </View>
      <Text className="w-full text-[12px] text-[#f0fffc] text-left leading-5"
          numberOfLines={3}
          ellipsizeMode="tail">
      {status}
      </Text>
    </View>
  </View>

  <View className="px-4 pb-5">
    <View className="rounded-2xl overflow-hidden border border-white/20 bg-white/90">
      <Image source={require('../../images/bg/bgwhiteAIVER.jpeg')} className="w-full h-14 object-contain" />
    </View>
  </View>
</View>

  );
};


const ListaScreen: React.FC<{session: (value: boolean) => void, menuStatus:boolean, setMenuStatus:(value:boolean)=>void}> = ({session, menuStatus, setMenuStatus}) => {
  const events = ['pointermove', 'pointerdown', 'pointerup']
  const [active, setActive] = useState('Active')
  const [isReportActive, setIsReportActive] = useState(false)
  //const [content, setContent] = useState<React.ReactNode | null>(!menuStatus?<NetSuiteLoginForm setMenuStatus={setMenuStatus} isReportActive={isReportActive} setIsReportActive={setIsReportActive}/>:<TailwindAdaptedComponent isReportActive={isReportActive} setIsReportActive={setIsReportActive}/>);
  const [activeIndex, setActiveIndex] = useState<number>(!menuStatus?10:1)
  const timerActiveRef = useRef(false);
  const inactivityTimerRef = useRef<any>(null);

  const maxInactivityTime = 30*60000;

  const menuIndex: MenuIndex[] = [
    { id: 1, component: <TailwindAdaptedComponent isReportActive={isReportActive} session={session}/> },
    { id: 2, component: <AnalysisComponent isReportActive={isReportActive} session={session} /> },
    //{ id: , component: null },
    { id: 3, component: null },
    // { id: , component: <RoleuserComponent /> },
    // { id: , component: <RolepermissionsComponent /> },
    { id: 4, component: <Roles session={session} /> },
    { id: 5, component: <Employees session={session} /> },
    { id: 6, component: <Subsidiaries session={session} /> },
    { id: 7, component: <GlobalPermissions session={session} /> },
    { id: 8, component: <Relationships session={session} /> },
    { id: 9, component: <SOD session={session} /> },
    // { id: , component: null },
    // { id: , component: null },
    // { id: , component: null },
    // { id: , component: null },
    { id: 10, component: <NetSuiteLoginForm setMenuStatus={setMenuStatus} isReportActive={isReportActive} setIsReportActive={setIsReportActive} session={session} /> },
    // { id: , component: null },
    // { id: , component: <Registro /> },
    // { id: , component: <Ticketing /> },
    { id: 11, component: <AIAnalysis session={session} /> },
    { id: 12, component: null },   
  ];

  const handleSessionExpiry = async() => {
    if (timerActiveRef.current){
      timerActiveRef.current = false;
      if (inactivityTimerRef.current){
        clearTimeout(inactivityTimerRef.current);
      }
      await logout(session)
    }
  }

  const resetInactivityTimer = () => {
    if (timerActiveRef.current==false){
      timerActiveRef.current = true;
    }
    if (inactivityTimerRef.current){
      clearTimeout(inactivityTimerRef.current);
    }
    inactivityTimerRef.current = setTimeout(handleSessionExpiry, maxInactivityTime)
  }

  useEffect(()=>{

    const sessionData = getSessionData()
    if (sessionData.Company && sessionData.UserID){
      WebSocketsService.newSocket(`${sessionData.Company}_${sessionData.UserID}_${sessionData.WebSocketID}`, setActive, setIsReportActive);
    }

    events.forEach((event) => {window.addEventListener(event, resetInactivityTimer)});
    resetInactivityTimer();

    return () => {
      if (inactivityTimerRef.current){
        clearTimeout(inactivityTimerRef.current);
      }
      events.forEach((event) => {window.removeEventListener(event, resetInactivityTimer)});
    };
  }, [])

  const loadPage = (id: number) => {
    const selected = menuIndex.find((item) => item.id === id);
    return selected?.component
  };

  return (
     <ScrollView
      contentContainerStyle={{ flexGrow: 1 }}
    >
      <View className="flex w-full min-h-screen min-h-[100dvh] flex-col bg-[#f4f4f4] lg:flex-row" style={{
        backgroundColor: '#f4f4f4',
      }}>
        <NavigationMenu setActiveIndex={setActiveIndex} session={session} status={active} menuStatus={menuStatus} setMenuStatus={setMenuStatus} isReportActive={isReportActive} setIsReportActive={setIsReportActive}/>
        <View className="flex-1 bg-[#f4f4f4]"
          style={{
            flex: 1,
            minWidth: 320,
            backgroundColor: '#f4f4f4',
          }}
        >
          <ScrollView contentContainerStyle={{ minHeight: '100%' }}>
            {loadPage(activeIndex)}
          </ScrollView>
        </View>
      </View>
     </ScrollView>
  );
};

export default ListaScreen;
