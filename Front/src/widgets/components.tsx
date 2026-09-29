import React from 'react';
import { FilterTable } from './filterTable';

export const Header: React.FC<{ title: string }> = ({ title }) => {
    return (
        <div className="flex items-center justify-center h-[110px] bg-gradient-to-r from-[#0d1b2a] via-[#13263c] to-[#0b1724] border-b border-white/10 shadow-[0_20px_60px_rgba(4,20,32,0.45)]">
            <span className="text-center text-white tracking-[0.12em] font-extrabold text-5xl uppercase">{title}</span>
        </div>
    )    
};

export const Body: React.FC<{ endpoint: string, session:(value:boolean)=>void, fullHeight?: boolean }> = ({ endpoint, session, fullHeight = true }) => {
    const wrapperClass = fullHeight ? 'flex-1 min-h-0 h-[calc(100vh-100px)] overflow-hidden p-4 space-y-8' : 'flex-1 min-h-0 h-full overflow-hidden p-4 space-y-8'

    return (
        <div className={wrapperClass}>
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg w-full h-full overflow-hidden">
                <div className="p-4 w-full h-full min-h-0 flex flex-col">
                    <div className="w-full h-full rounded overflow-hidden flex flex-col min-h-0">
                        <div className="flex-1 min-h-0 h-full overflow-hidden">
                            <FilterTable endpoint={endpoint} session={session}></FilterTable>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
};

export const Component: React.FC<{ title: string, endpoint: string, session:(value:boolean)=>void }> = ({ title, endpoint, session }) => {
    return (
        <div className="flex flex-col h-screen bg-gray-100 min-w-[320px] w-full overflow-hidden">
            <Header title={title}></Header>
            <Body endpoint={endpoint} session={session}></Body>
        </div>
    )
}