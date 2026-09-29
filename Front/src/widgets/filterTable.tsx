import { FilterMatchMode, FilterOperator } from 'primereact/api';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { MultiSelect } from 'primereact/multiselect';
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { getSessionData } from '../services/storage';
import { httpRequest } from '../services/generalService';
import React from 'react';
import { Checkbox } from 'primereact/checkbox';
import { InputText } from 'primereact/inputtext';

type FilterTableRef = {
  createSODRule: () => void;
  removeSelectedSODRules: () => void;
  resetSODRules: () => void;
};

type FilterTableProps = {
  endpoint: string;
  filter?: any;
  specialFeatures?: boolean;
  session: (value: boolean) => void;
};

function FilterTableComponent(
  { endpoint, filter = null, specialFeatures = false, session }: FilterTableProps,
  ref: React.ForwardedRef<FilterTableRef>
) {
    const dataProps = {
        title: '',
        columns: [],
        data: [],
        uniques: {},
        fileName: ''
    }
    const [data, setData] = useState(dataProps);
    const [filters, setFilters] = useState({});
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [selectedRows, setSelectedRows] = useState([]);
    const dt:any = useRef(null);
    const [pageLinkSize, setPageLinkSize] = useState(5);
    const [paginatior, setPaginator] = useState<any>([0]);

    useEffect(() => {
        const getData = async() => {
          const sessionData = getSessionData();
          if (sessionData && sessionData.Company) {
            let sessionDataFilter:any = { ...sessionData }
            if (filter) {
              sessionDataFilter = { ...sessionData, filter: filter}
            }
            const response = await httpRequest('POST', endpoint, sessionDataFilter);
            if (!response) {
              setLoadError('Unable to connect to the backend. Please refresh or check the server.');
              setIsLoading(false);
              return;
            }
            if (response.detail){
              setData({
                title: response.detail,
                columns: [],
                data: [],
                uniques: {},
                fileName: ''
              })
            }else{
              let responseFilters:any = {}
              if (Array.isArray(response.columns)) {
                for (let i=0; i<response.columns.length; i++) {
                  responseFilters[response.columns[i]] = {value:null, matchMode:FilterMatchMode.IN}
                }
              }
              setFilters(responseFilters)
              setData(response)
            }
            setIsLoading(false)

            const temp_paginator = []
            const options = [50, 100, 250, 500]
            const rowsLength = Array.isArray(response?.data) ? response.data.length : 0
            for (let i=0; i<4; i++){
              let page_size = options[i]
              if (page_size < rowsLength) {
                temp_paginator.push(page_size)
              } else {
                temp_paginator.push(rowsLength)
                break
              }
            }
            setPaginator(temp_paginator)
          }else{
            session(false)
          }
        }
        getData()

        const handleResize = () => {
          const width = window.innerWidth;
      
          if (width <= 450) setPageLinkSize(2);
          else if (width <= 500) setPageLinkSize(3);
          else if (width <= 600) setPageLinkSize(4);
          else setPageLinkSize(5);
        };
      
        handleResize(); // set inicial
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

  const createSODRule = async () => {
    const sessionData = await getSessionData();
    if (sessionData && sessionData.Company){
      if (!isLoading) {
        console.log('You have clicked on the "createSODRule" function.')
      }
    }else{
      session(false)
    }
  }

  const removeSODRules = async () => {
    const sessionData = await getSessionData()
    if (sessionData && sessionData.Company){
      if (!isLoading) {
        if (selectedRows && selectedRows.length>0) {
          if (window.confirm('Are you sure you want to remove the selected SOD rules?')){
            const rules:any = []
            selectedRows.forEach(element => {
              const rule = {
                RiskId: element["Risk Id"],
                SecurityObjectLabel: element["SECURITY OBJECT LABEL"]
              }
              rules.push(rule)
            });
            if (rules.length>0){
              const newSessionData = {...sessionData, SODRules: rules}
              const response = await httpRequest('POST', '/remove_selected_SOD_rules', newSessionData)
              if (response && response.detail){
                window.alert(response.detail)
              }else{
                const rulesFiltered = data.data.filter(
                  object => !selectedRows.some(eliminar => eliminar["Risk Id"]==object["Risk Id"] && eliminar["SECURITY OBJECT LABEL"]==object["SECURITY OBJECT LABEL"])
                )
                const newData:any = {...data, data: rulesFiltered}
                setData(newData);
                setSelectedRows([])
                window.alert('Selected SOD rules have been removed successfully.')
              }
            }
          }
        }
      }
    }else{
      session(false)
    }
  }

  const resetSODRules = async () => {
    const sessionData = await getSessionData();
    if (sessionData && sessionData.Company){
      if (!isLoading) {
        if (data.data && data.data.length>0) {
          if (window.confirm('Are you sure to remove all your SOD rules?')) {
            const response = await httpRequest('POST', '/remove_all_personal_SOD_RuleSet', sessionData)
            if (response && response.detail){
              window.alert(response.detail)
            }else{
              const newData:any = {...data, data: []}
              setData(newData);
              window.alert('All SOD rules have been removed successfully.')
            }
          }
        }
      }
    }else{
      session(false)
    }
  }

  useImperativeHandle(ref, () => ({
    createSODRule: createSODRule,
    removeSelectedSODRules: removeSODRules,
    resetSODRules: resetSODRules,
  }))

  const onCheckboxChange = async (rowData:any, checked:any) => {
    const sessionData = getSessionData()
    if (sessionData && sessionData.Company){
      const updateSODRuleSet = {
        ...sessionData,
        SODRule: {
          RiskId: rowData['Risk Id'],
          SecurityObjectLabel: rowData['SECURITY OBJECT LABEL'],
          Enabled: checked,
          TableType: endpoint.startsWith('/personal_') 
        }
      }
      const response = await httpRequest('PUT', '/change_SOD_Rule_status', updateSODRuleSet)
      if (response && response.detail){
        window.alert(response.detail)
      }else{
        const updatedData = data.data.map((item:any) =>
          item['Risk Id'] === rowData['Risk Id']  && item['SECURITY OBJECT LABEL'] === rowData['SECURITY OBJECT LABEL'] ? { ...item, ENABLED: checked?1:0 } : item
        );
        const newData:any = {...data, data: updatedData}
        setData(newData);
      }
    }else{
      session(false)
    }
  };

  const valueBodyTemplate = (rowData:any, key:string) => {
    return (
      key=='ENABLED'?
        <React.Fragment>
            <Checkbox className='flex justify-center' 
              checked={rowData[key]==1}
              onChange={async (e) => await onCheckboxChange(rowData, e.checked)}
              disabled={filter==null?false:true}
            />
        </React.Fragment>
      :
        <React.Fragment>
            <span className="text-gray-700">{rowData[key]}</span>
        </React.Fragment>
    );
  }

  const valueRowFilterTemplate = (options: any, data: any) => {
    return <MultiSelect
      value={options.value || []}
      options={data}
      itemTemplate={valueItemTemplate}
      onChange={(e) => options.filterApplyCallback(e.value)}
      optionLabel="value"
      placeholder="Any"
      panelStyle={{ 
        backgroundColor: '#ffffff',
        border: '1px solid #e5e7eb',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
      }}
      className="bg-white border border-gray-300 rounded-md shadow-sm text-gray-800 w-full"
      display="chip"
      filter
      filterIcon="null"
      filterPlaceholder="Search..."
      maxSelectedLabels={2}
    />;
  }

  const valueItemTemplate = (option:any) => {
    return (
        <div className="p-multiselect-representative-option text-gray-700">
            <span>{option.value}</span>
        </div>
    );
  }

  const exportCSV = (selectionOnly:any) => {
    if (dt.current){
      dt.current.exportCSV({ selectionOnly });
    }
  }

  const onRowEditComplete = async (e:any) => {
    let _SODRules:any = [...data.data];
    let { newData, index } = e;
    _SODRules[index] = newData;
    const newSODRules = {...data, data:_SODRules}
    setData(newSODRules);
  };

  const textEditor = (options:any) => {
    const sessionData = getSessionData()
    if (sessionData && sessionData.Company){
      return <InputText value={options.value} onChange={(e) => options.editorCallback(e.target.value)} />;
    }else{
      session(false)
      return null;
    }
  };

  return (
    <div className='flex flex-col min-h-0 h-full'>
      {/*
        <Text className="text-center text-gray-800 text-xl font-semibold mb-6">
            {data.title}
        </Text>
      */}
      <div className='flex flex-row items-center justify-between bg-slate-500 rounded-t-lg px-4 py-4 flex-wrap'>
        <div className="flex-1 items-center">
          <span className="text-xl font-semibold text-white text-center">
            {data.title}
          </span>
        </div>
        <button
          disabled={isLoading && (data.title=='' || data.title=='Loading Error')} 
          onClick={() => exportCSV(false)} 
          style={{ flexShrink: 1, backgroundColor: '#3ED402', width: 'auto', height: 'auto', borderRadius: 5, alignItems: 'center', justifyContent: 'center', padding: 4 }}>
          <span style={{ color: 'white', fontWeight: 'bold' }}>Export CSV</span>
        </button>
      </div>
      <div className='flex-1 min-h-0 w-full overflow-hidden h-full'>
        {loadError ? (
          <div className='flex h-full min-h-[160px] items-center justify-center rounded-lg border border-red-300 bg-red-50 p-6 text-center'>
            <div>
              <p className='mb-2 text-lg font-semibold text-red-700'>Connection error</p>
              <p className='text-sm text-red-600'>{loadError}</p>
            </div>
          </div>
        ) : (
          <DataTable
            ref={dt}
            exportFilename={data.fileName}
            key='id'
          value={data.data}
          paginator
          rows={paginatior[0]}
          rowsPerPageOptions={paginatior}
          pageLinkSize={pageLinkSize}
          responsiveLayout="scroll"
          breakpoint="960px"
          paginatorTemplate={{
            layout: 'FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown',
            
            CurrentPageReport: (options) => (
              <span className="text-base hidden sm:inline">
                {options.first} to {options.last} of {options.totalRecords}
              </span>
            ),
          }}
          filters={filters}
          filterDisplay="row"
          loading={isLoading}
          globalFilterFields={data.columns}
          showGridlines
          stripedRows
          removableSort
          scrollable
          scrollHeight="flex"
          className="p-datatable-sm border border-gray-300 rounded-lg min-w-full h-full min-h-0"
          style={{ minHeight: 0, height: '100%', overflow: 'hidden' }}
          pt={{
            header: { className: 'bg-gray-100' },
            paginator: { 
              root: { className: 'border-t-[1px] border-gray-300 rounded-b-lg bg-gray-50 p-3 flex justify-between items-center text-black' },
              pageButton: { className: 'px-3 py-1 mx-1 rounded-md text-gray-700 hover:bg-gray-200 text-black' }
            }
          }}
          style={{ minHeight: 0, height: '100%' }}
          selectionMode={specialFeatures ? "multiple" : null}
          selection={selectedRows}
          dragSelection={specialFeatures}
          onSelectionChange={(e:any) => {setSelectedRows(e.value)}}
          editMode={specialFeatures?"row":""}
          onRowEditComplete={async (e:any) => {await onRowEditComplete(e)}}
        >
          {specialFeatures && <Column rowEditor />}
          {data.columns.map((value, index) => (
            <Column
              key={index}
              filterMenuStyle={{ 
                backgroundColor: '#ffffff',
                minWidth: '16rem', 
                border: '1px solid #e5e7eb',
              }}               
              header={value}
              field={value}
              filterField={value}
              showFilterMenu={false}
              filterHeaderStyle={{ 
                backgroundColor: 'white',
              }}
              body={(rowData) => valueBodyTemplate(rowData, value)}
              filter
              filterElement={(options) => valueRowFilterTemplate(options, data.uniques[value])}
              sortable
              className="border-r-[1px] border-gray-300 last:border-r-0 w-auto"
              headerStyle={{ 
                backgroundColor: '#f8f9fa',
                color: '#374151',
                fontWeight: '600',
                textAlign: 'center',
                borderBottom: '2px solid #e5e7eb',
                borderTop: '2px solid #e5e7eb',
                padding: '1rem',
                whiteSpace: 'nowrap',
              }}
              bodyStyle={{ 
                padding: '0.75rem',
                borderBottom: '1px solid #f3f4f6',
                fontSize: '0.875rem',
                color: 'gray-800'
              }}
              editor={(options) => textEditor(options)}
            />
          ))}
        </DataTable>
          )}
      </div>
    </div>
  )
}

export const FilterTable = forwardRef<FilterTableRef, FilterTableProps>(FilterTableComponent);